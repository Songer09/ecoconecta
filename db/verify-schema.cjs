// Regression check against an EMPTY, disposable PostgreSQL database only.
// No application dependency: provide node-postgres through NODE_PATH.
const { Client } = require('pg');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

async function main() {
  if (process.env.ECOCONECTA_SCHEMA_TEST !== '1') {
    throw new Error('Set ECOCONECTA_SCHEMA_TEST=1 for an isolated schema test');
  }
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  let passed = 0;
  let sequence = 0;
  const query = (sql, values) => client.query(sql, values);
  const id = async (sql, values) => (await query(sql + ' RETURNING id', values)).rows[0].id;
  async function flush() {
    await query('SET CONSTRAINTS ALL IMMEDIATE');
    await query('SET CONSTRAINTS ALL DEFERRED');
  }
  async function rejects(label, sql, values, code) {
    const savepoint = 'check_' + ++sequence;
    await query('SAVEPOINT ' + savepoint);
    let error;
    try { await query(sql, values); await flush(); } catch (err) { error = err; }
    await query('ROLLBACK TO SAVEPOINT ' + savepoint);
    await query('RELEASE SAVEPOINT ' + savepoint);
    assert.ok(error, label + ': expected rejection');
    assert.equal(error.code, code, label);
    console.log('PASS', label);
    passed++;
  }
  await client.connect();
  try {
    const database = (await query('SELECT current_database() AS name')).rows[0].name;
    assert.equal(database, 'ecoconecta_schema_test', 'Refusing a non-test database');
    const tables = await query("SELECT tablename FROM pg_tables WHERE schemaname = 'public'");
    assert.equal(tables.rowCount, 0, 'Refusing a nonempty database');
    // Atomic schema load. The script never drops existing objects or databases.
    await query('BEGIN');
    await query(fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8'));
    await query('COMMIT');
    console.log('PASS schema creates on PostgreSQL'); passed++;
    await query('BEGIN');
    const requester = await id("INSERT INTO users(full_name, phone, role) VALUES ('Synthetic requester', '+00000000001', 'solicitante')");
    const coordinator = await id("INSERT INTO users(full_name, phone, role) VALUES ('Synthetic coordinator', '+00000000002', 'coordinador_huerteros')");
    const collector = await id("INSERT INTO users(full_name, phone, role) VALUES ('Synthetic collector', '+00000000003', 'recolector')");
    const collective = await id("INSERT INTO collectives(name, flow) VALUES ('Synthetic collective', 'organico')");
    const zone = await id("INSERT INTO zones(code,name) VALUES ('TEST','Synthetic zone')");
    await query("INSERT INTO collective_members(collective_id,user_id,member_role) VALUES ($1,$2,'coordinador'),($1,$3,'recolector')", [collective, coordinator, collector]);
    const newRequest = code => id("INSERT INTO pickup_requests(code,requester_id,collective_id,flow,zone_id,generator,contact_phone,address,source_channel) VALUES ($1,$2,$3,'organico',$4,'hogar','synthetic','synthetic','web')", [code,requester,collective,zone]);
    const request = await newRequest('TEST-1');
    const otherRequest = await newRequest('TEST-2');
    const assignment = await id('INSERT INTO request_assignments(request_id,coordinator_id,collector_id) VALUES ($1,$2,$3)', [request,coordinator,collector]);
    await flush();
    await rejects('one current assignment', 'INSERT INTO request_assignments(request_id,coordinator_id,collector_id) VALUES ($1,$2,$3)', [request,coordinator,collector], '23505');
    await rejects('schedule cannot reference another request assignment', 'INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,created_by,confirmed_by) VALUES ($1,$2,now(),$3,$3)', [otherRequest,assignment,coordinator], '23503');
    await rejects('scheduled requires schedule', "UPDATE pickup_requests SET status='programada' WHERE id=$1", [request], '23514');
    await query('INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,created_by,confirmed_by) VALUES ($1,$2,now(),$3,$3)', [request,assignment,coordinator]);
    await query("UPDATE pickup_requests SET status='programada' WHERE id=$1", [request]);
    await flush();
    await rejects('one current schedule', 'INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,created_by,confirmed_by) VALUES ($1,$2,now(),$3,$3)', [request,assignment,coordinator], '23505');
    const material = await id("INSERT INTO waste_types(name,flow,unit) VALUES ('Synthetic A','organico','test-unit')");
    const secondMaterial = await id("INSERT INTO waste_types(name,flow,unit) VALUES ('Synthetic B','organico','test-unit')");
    const wrongMaterial = await id("INSERT INTO waste_types(name,flow,unit) VALUES ('Synthetic recyclable','reciclable','test-unit')");
    await rejects('material flow must match request', 'INSERT INTO request_items(request_id,waste_type_id) VALUES ($1,$2)', [request,wrongMaterial], '23514');
    const collection = await id('INSERT INTO collections(request_id,collector_id,assignment_id) VALUES ($1,$2,$3)', [request,collector,assignment]);
    await rejects('positive quantities', "INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit) VALUES ($1,$2,0,'test-unit')", [collection,material], '23514');
    await rejects('compatible material units', "INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit) VALUES ($1,$2,1,'wrong-unit')", [collection,material], '23514');
    const item = await id("INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit) VALUES ($1,$2,1,'test-unit')", [collection,material]);
    const secondItem = await id("INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit) VALUES ($1,$2,2,'test-unit')", [collection,secondMaterial]);
    const rule = await id("INSERT INTO points_rules(waste_type_id,points_per_unit,version,base_unit,description,valid_from,validated_by_fsd,created_by,approved_by) VALUES ($1,1,1,'test-unit','SYNTHETIC TEST ONLY','2000-01-01Z',TRUE,$2,$2)", [material,coordinator]);
    const secondRule = await id("INSERT INTO points_rules(waste_type_id,points_per_unit,version,base_unit,description,valid_from,validated_by_fsd,created_by,approved_by) VALUES ($1,1,1,'test-unit','SYNTHETIC TEST ONLY','2000-01-01Z',TRUE,$2,$2)", [secondMaterial,coordinator]);
    const creditSql = "INSERT INTO points_ledger(user_id,collection_id,collection_item_id,rule_id,base_quantity,base_unit,reason,points,idempotency_key,created_by) VALUES ($1,$2,$3,$4,$5,'test-unit','recoleccion',$5,gen_random_uuid(),$6)";
    const credit = [requester,collection,item,rule,1,coordinator];
    await rejects('no points before confirmation', creditSql, credit, '23514');
    await rejects('complete confirmation metadata', 'UPDATE collections SET confirmed_at=now() WHERE id=$1', [collection], '23514');
    await rejects('collected status requires confirmed collection', "UPDATE pickup_requests SET status='recolectada' WHERE id=$1", [request], '23514');
    await query('UPDATE collections SET confirmed_at=now(),confirmed_by=$2,confirmation_key=gen_random_uuid() WHERE id=$1', [collection,coordinator]);
    await query("UPDATE pickup_requests SET status='recolectada' WHERE id=$1", [request]);
    await query(creditSql,credit);
    await query(creditSql,[requester,collection,secondItem,secondRule,2,coordinator]);
    await flush();
    assert.equal(Number((await query('SELECT points_balance FROM requester_points_balances WHERE user_id=$1',[requester])).rows[0].points_balance),3);
    console.log('PASS complete flow, two materials and derived balance'); passed++;
    await rejects('no duplicate credit for same item',creditSql,credit,'23505');
    await rejects('ledger cannot be updated', 'UPDATE points_ledger SET points=99 WHERE collection_id=$1',[collection],'23514');
    await rejects('ledger cannot be truncated','TRUNCATE points_ledger',[],'23514');
    await rejects('used rule cannot be rewritten','UPDATE points_rules SET points_per_unit=99 WHERE id=$1',[rule],'23514');
    await rejects('confirmed quantities cannot change','UPDATE collection_items SET quantity=99 WHERE id=$1',[item],'23514');
    await rejects('confirmed closure cannot be rewritten','UPDATE collections SET result_notes=$2 WHERE id=$1',[collection,'changed'],'23514');
    await query("INSERT INTO webhook_events(provider,event_key,event_kind,provider_message_id) VALUES ('twilio','synthetic:sent','status','synthetic'),('twilio','synthetic:delivered','status','synthetic')");
    console.log('PASS distinct statuses for same provider message'); passed++;
    await rejects('duplicate webhook rejected',"INSERT INTO webhook_events(provider,event_key,event_kind) VALUES ('twilio','synthetic:sent','status')",[],'23505');
    await query('ROLLBACK'); // Synthetic fixtures never persist.
    console.log(`${passed} checks passed; synthetic fixtures rolled back.`);
  } finally {
    await query('ROLLBACK').catch(() => {});
    await client.end();
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
