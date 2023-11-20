const titleSplitter = ' > ';

export default class UrlData {
  static objectToData(data: any) {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
      return null;
    }

    return encodeURIComponent(JSON.stringify(data));
  }

  static set(data: any) {
    const hash = UrlData.objectToData(data);
    if (!hash) {
      window.history.pushState('', '/', window.location.pathname);
      return false;
    }
    window.location.hash = hash;
    return true;
  }

  static get() {
    try {
      const data = JSON.parse(decodeURIComponent(window.location.hash.substring(1)) || 'null');
      // eslint-disable-next-line no-console
      console.log(data);
      return data;
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
      try {
        const data = JSON.parse(decodeURIComponent(decodeURIComponent(window.location.hash.substring(1))) || 'null');
        // eslint-disable-next-line no-console
        console.log(data);
        return data;
      } catch (e2) {
        // eslint-disable-next-line no-console
        console.error(e2);
      }
    }
    return null;
  }

  static getKey(key: string) {
    const data = UrlData.get();

    if (!data || typeof data !== 'object') {
      return undefined;
    }

    return data[key];
  }

  static title(newTitle: string) {
    const baseTitleSplit = window.document.title.split(titleSplitter);
    const baseTitle = baseTitleSplit.length > 1 ? baseTitleSplit[1] : baseTitleSplit[0];
    if (newTitle) {
      window.document.title = newTitle + titleSplitter + baseTitle;
    } else {
      window.document.title = baseTitle;
    }
  }
}
