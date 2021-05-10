const titleSplitter = ' > ';

export default class UrlData {
  static set(data) {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
      window.history.pushState('', '/', window.location.pathname);
      return false;
    }
    window.location.hash = JSON.stringify(data);
    return true;
  }

  static get() {
    try {
      const data = JSON.parse(decodeURI(window.location.hash.substring(1)) || 'null');
      console.log(data);
      return data;
    } catch (e) {
      console.error(e);
    }
    return null;
  }

  static title(newTitle) {
    const baseTitleSplit = window.document.title.split(titleSplitter);
    const baseTitle = baseTitleSplit.length > 1 ? baseTitleSplit[1] : baseTitleSplit[0];
    if (newTitle) {
      window.document.title = newTitle + titleSplitter + baseTitle;
    } else {
      window.document.title = baseTitle;
    }
  }
}
