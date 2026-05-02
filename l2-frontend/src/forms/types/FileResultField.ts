export type ExistingFileFieldValueFile = {
  pk: number
  originalName: string
  extension: string
  mimeType: string
  size: number
  url: string
  createdAt: string
  isNew?: false
}

export type NewFileFieldValueFile = {
  tempId: string
  originalName: string
  extension: string
  mimeType: string
  size: number
  file: File
  isNew: true
}

export type FileFieldValueFile = ExistingFileFieldValueFile | NewFileFieldValueFile

export type FileFieldValue = FileFieldValueFile[]
