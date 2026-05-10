export type SelectOption = {
  id: string | number
  label: string
}

export type BackendFileFieldDefaults = {
  min_files: number
  max_files: number
  max_file_size_mb: number
  max_total_size_mb: number
  allowed_extensions: string[]
}

export type FileFieldConstructorSettings = {
  fileFieldLimits: {
    max_files: number
    max_file_size_mb: number
    max_total_size_mb: number
  }
  fileFieldDefaultSettings: BackendFileFieldDefaults
  fileFieldAllowedExtensions: string[]
};
