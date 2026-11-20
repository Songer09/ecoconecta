// Invoked by start-local-postgres.ps1; credentials arrive through environment only.
const { Client } = require('pg');
const fs = require('node:fs');
const path = require('node:path');
const literal = value => "'" + value.replaceAll("'", "''") + "'";
async function connect(user, password, database = 'postgres') {
  const client = new Client({ host: '127.0.0.1', port: 5432, user, password, database });
  await client.connect();
  return client;
}
async function main() {
  const admin = await connect('postgres', process.env.ECO_PG_ADMIN_PASSWORD);
  try {
    for (const [name, password] of [
      ['ecoconecta_owner', process.env.ECO_PG_OWNER_PASSWORD],
      ['ecoconecta_app', process.env.ECO_PG_APP_PASSWORD],
    ]) {
      if (!(await admin.query('SELECT 1 FROM pg_roles WHERE rolname=$1', [name])).rowCount) {
        await admin.query(`CREATE ROLE ${name} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD ${literal(password)}`);
      }
    }
    if (!(await admin.query("SELECT 1 FROM pg_database WHERE datname='ecoconecta'")).rowCount) {
      await admin.query('CREATE DATABASE ecoconecta OWNER ecoconecta_owner');
    }
  } finally { await admin.end(); }
  const owner = await connect('ecoconecta_owner', process.env.ECO_PG_OWNER_PASSWORD, 'ecoconecta');
  try {
    const tables = await owner.query("SELECT tablename FROM pg_tables WHERE schemaname='public'");
    if (!tables.rowCount) {
      await owner.query('BEGIN');
      try {
        await owner.query(fs.readFileSync(path.join(__dirname, '..', 'db', 'schema.sql'), 'utf8'));
        await owner.query('COMMIT');
      } catch (error) { await owner.query('ROLLBACK'); throw error; }
    } else {
      const expected = ['users','zones','pickup_requests','collections','points_ledger','webhook_events'];
      if (!expected.every(name => tables.rows.some(row => row.tablename === name))) {
        throw new Error('Existing schema differs: inspect it and use a migration; no tables were overwritten');
      }
      console.log('Existing schema preserved; changes require Alembic migrations.');
    }
    await owner.query(`
      REVOKE ALL ON DATABASE ecoconecta FROM PUBLIC;
      GRANT CONNECT ON DATABASE ecoconecta TO ecoconecta_app;
      REVOKE CREATE ON SCHEMA public FROM PUBLIC;
      GRANT USAGE ON SCHEMA public TO ecoconecta_app;
      GRANT SELECT, INSERT, UPDATE ON users, consents, requester_profiles, collectives,
        collective_members, zones, collector_zone_coverage, availability_slots, collection_schedules,
        waste_types, points_rules, pickup_requests, request_items, request_assignments,
        request_schedules, request_status_history, collections, collection_items, points_ledger,
        educational_content, whatsapp_messages, webhook_events, chat_conversations, chat_messages,
        chat_tool_calls, chat_faq, audit_log TO ecoconecta_app;
      REVOKE UPDATE ON points_ledger, audit_log FROM ecoconecta_app;
      REVOKE ALL ON requester_points_balances FROM ecoconecta_app;
      GRANT SELECT ON requester_points_balances TO ecoconecta_app;
    `);
  } finally { await owner.end(); }
  const app = await connect('ecoconecta_app', process.env.ECO_PG_APP_PASSWORD, 'ecoconecta');
  try {
    const result = await app.query(`SELECT current_database() AS database,
      (SELECT COUNT(*)::int FROM pg_tables WHERE schemaname='public') AS tables,
      (SELECT rolsuper OR rolcreatedb OR rolcreaterole FROM pg_roles WHERE rolname=current_user) AS privileged`);
    if (result.rows[0].privileged) throw new Error('Runtime role has excessive privileges');
    console.log(`PostgreSQL ready: 127.0.0.1:5432 / ${result.rows[0].database}; ${result.rows[0].tables} tables; runtime role without administrative privileges.`);
  } finally { await app.end(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
