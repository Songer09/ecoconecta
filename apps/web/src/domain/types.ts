export type Role = 'neighbor' | 'collector' | 'vivi' | 'kelly' | 'admin'
export type RequestFlow = 'RECYCLABLE' | 'ORGANIC'
export type RequestStatus = 'RECEIVED' | 'UNDER_REVIEW' | 'ASSIGNED' | 'SCHEDULED' | 'COLLECTED' | 'COMPLETED' | 'CANCELLED'

export interface CollectionRequest {
  id: string
  flow: RequestFlow
  status: RequestStatus
  createdAt: string
  stage: string
  neighborhood: string
  tower: string
  apartment: string
  materials: string[]
  note: string
  availability: string
  assignedTo?: string
  scheduledAt?: string
  collectedAt?: string
}

export interface NewRequest {
  flow: RequestFlow
  stage: string
  neighborhood: string
  tower: string
  apartment: string
  materials: string[]
  note: string
  availability: string
}

export interface EducationTopic {
  id: string
  title: string
  summary: string
  minutes: number
  body: string[]
}

export interface EcoConectaService {
  listRequests(): Promise<CollectionRequest[]>
  createRequest(input: NewRequest): Promise<CollectionRequest>
  assignRequest(id: string, collectorName: string, scheduledAt: string): Promise<CollectionRequest>
  registerCollection(id: string): Promise<CollectionRequest>
  verifyAndClose(id: string): Promise<CollectionRequest>
  listEducationTopics(): EducationTopic[]
  getCompletedTopics(): string[]
  setTopicCompleted(id: string, completed: boolean): void
}
