export type FileFieldValueFile = {
  pk: number
  originalName: string
  extension: string
  mimeType: string
  size: number
  url: string
  createdAt: string
}

export type FileFieldValue = FileFieldValueFile[]
