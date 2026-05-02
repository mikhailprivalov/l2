export type FileRulesMode = 'exact' | 'oneOf'

export type FileRuleItem = {
  extension: string
  count: number
}

export type FileRuleVariant = {
  items: FileRuleItem[]
}

export type FileFieldSettings = {
  minFiles: number | null
  maxFiles: number | null
  maxFileSizeMb: number | null
  maxTotalSizeMb: number | null

  allowedExtensions: string[]

  filenamePattern: string
  filenamePatternDescription: string
  strictFilename: boolean

  rulesEnabled: boolean
  rulesMode: FileRulesMode
  rulesVariants: FileRuleVariant[]
}
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
