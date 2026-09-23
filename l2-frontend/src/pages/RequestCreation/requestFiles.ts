export type RequestFileLimits = {
  maxTotalBytes: number;
  maxTotalMb: number;
  extensions: string[];
};

const DEFAULT_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'dcm'];

export function requestFileLimitsFromModules(modules: Record<string, unknown> | undefined): RequestFileLimits {
  const mbRaw = Number(modules?.request_creation_files_max_total_mb);
  const maxTotalMb = Number.isFinite(mbRaw) && mbRaw > 0 ? mbRaw : 10;
  const raw = modules?.request_creation_file_extensions;
  const source = Array.isArray(raw) ? raw : DEFAULT_EXTENSIONS;
  const extensions = source
    .map((item) => String(item).trim().toLowerCase().replace(/^\./, ''))
    .filter(Boolean);
  return {
    maxTotalBytes: maxTotalMb * 1024 * 1024,
    maxTotalMb,
    extensions,
  };
}

export function requestFileHint(limits: RequestFileLimits): string {
  const extensions = limits.extensions.length ? `, ${limits.extensions.join(', ')}` : '';
  return `Добавить файлы (до ${limits.maxTotalMb} МБ${extensions})`;
}

export function requestFileAccept(limits: RequestFileLimits): string | undefined {
  if (!limits.extensions.length) {
    return undefined;
  }
  return limits.extensions.map((ext) => `.${ext}`).join(',');
}

function fileExtension(name: string): string {
  const base = name.split(/[/\\]/).pop() || name;
  const dot = base.lastIndexOf('.');
  if (dot <= 0) {
    return '';
  }
  return base.slice(dot + 1).toLowerCase();
}

export function takeRequestFiles(
  incoming: File[],
  already: File[],
  extraBytes: number,
  limits: RequestFileLimits,
): { accepted: File[]; errors: string[] } {
  const errors: string[] = [];
  const accepted = [...already];
  let total = extraBytes + already.reduce((sum, file) => sum + file.size, 0);
  let totalExceeded = false;

  incoming.forEach((file) => {
    const extension = fileExtension(file.name);
    if (limits.extensions.length && !limits.extensions.includes(extension)) {
      errors.push(`Файл «${file.name}» имеет недопустимое расширение`);
      return;
    }
    if (total + file.size > limits.maxTotalBytes) {
      totalExceeded = true;
      return;
    }
    total += file.size;
    accepted.push(file);
  });

  if (totalExceeded) {
    errors.push(`Суммарный размер файлов превышает ${limits.maxTotalMb} МБ`);
  }
  return { accepted, errors };
}
