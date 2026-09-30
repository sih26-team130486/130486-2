export const documentService = {
  validateFile(file) {
    const allowed = ['application/pdf','image/jpeg','image/png','text/plain','text/csv',
      'application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/zip'];
    return Boolean(file) && (allowed.includes(file.type) || /\.(pdf|jpe?g|png|txt|csv|docx?|zip)$/i.test(file.name));
  },
  createDownload(blob, name) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = name; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
};
