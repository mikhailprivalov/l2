export type ParaclinicResultPayload = Record<string, any>;

type FilePayloadItem = {
  pk?: number
  tempId?: string
  isNew?: boolean
  originalName?: string
  extension?: string
  mimeType?: string
  size?: number
  file?: File
  [key: string]: any
};

const FILE_FIELD_TYPE = 42;
const FILE_FORM_DATA_KEY_PREFIX = 'paraclinic_file';

const isPlainObject = (value: any): value is Record<string, any> => value !== null && typeof value === 'object' && !Array.isArray(value) && !(value instanceof File)
    && !(value instanceof Blob);

const cloneValue = (value: any): any => {
  if (Array.isArray(value)) {
    return value.map(cloneValue);
  }

  if (isPlainObject(value)) {
    const result: Record<string, any> = {};

    for (const key of Object.keys(value)) {
      result[key] = cloneValue(value[key]);
    }

    return result;
  }

  return value;
};

const buildFilesManifest = (
  fieldPk: number | string,
  files: FilePayloadItem[],
  formData: FormData,
): { manifest: FilePayloadItem[]; hasNewFiles: boolean } => {
  const manifest: FilePayloadItem[] = [];
  let hasNewFiles = false;

  for (const file of files || []) {
    if (file && file.isNew && file.file instanceof File && file.tempId) {
      const key = `${FILE_FORM_DATA_KEY_PREFIX}:${fieldPk}:${file.tempId}`;

      formData.append(key, file.file, file.originalName || file.file.name);

      manifest.push({
        tempId: file.tempId,
        isNew: true,
        originalName: file.originalName || file.file.name,
        extension: file.extension || '',
        mimeType: file.mimeType || file.file.type || '',
        size: typeof file.size === 'number' ? file.size : file.file.size,
      });

      hasNewFiles = true;
      continue;
    }

    if (file && typeof file.pk === 'number') {
      manifest.push({
        pk: file.pk,
        originalName: file.originalName,
        extension: file.extension,
        mimeType: file.mimeType,
        size: file.size,
      });
    }
  }

  return { manifest, hasNewFiles };
};

export function buildParaclinicResultFormData(payload: ParaclinicResultPayload): {
  jsonPayload: ParaclinicResultPayload;
  formData: FormData | null;
} {
  const jsonPayload = cloneValue(payload) as ParaclinicResultPayload;
  const formData = new FormData();
  let hasNewFiles = false;

  const groups = jsonPayload?.data?.research?.groups;

  if (Array.isArray(groups)) {
    for (const group of groups) {
      const fields = group?.fields;

      if (!Array.isArray(fields)) {
        continue;
      }

      for (const field of fields) {
        if (field?.field_type !== FILE_FIELD_TYPE) {
          continue;
        }

        const { manifest, hasNewFiles: groupHasNewFiles } = buildFilesManifest(field.pk, field.files || [], formData);

        field.files = manifest;

        if (groupHasNewFiles) {
          hasNewFiles = true;
        }
      }
    }
  }

  return {
    jsonPayload,
    formData: hasNewFiles ? formData : null,
  };
}
