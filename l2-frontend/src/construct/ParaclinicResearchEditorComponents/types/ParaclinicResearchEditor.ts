export type GetRefBooksResponse = {
  file_field_limits: {
    max_files: number
    max_file_size_mb: number
    max_total_size_mb: number
  }
  file_field_default_settings: {
    min_files: number
    max_files: number
    max_file_size_mb: number
    max_total_size_mb: number
    allowed_extensions: string[]
  }
  file_field_allowed_extensions: string[]
}
