export const isSupportedDocument = (file: File) =>
  file.type === 'application/pdf' || file.name.endsWith('.txt');
