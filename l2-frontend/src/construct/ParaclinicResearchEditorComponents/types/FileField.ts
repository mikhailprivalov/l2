export type FileRulesMode = 'exact' | 'one_of'

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

  checkMime: boolean
  blockDoubleExtension: boolean
  sanitizeFilename: boolean

  filenamePattern: string
  filenamePatternDescription: string
  strictFilename: boolean

  rulesEnabled: boolean
  rulesMode: FileRulesMode
  rulesVariants: FileRuleVariant[]
}
