export default class UrlData {
  static set(data) {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
      window.history.pushState('', '/', window.location.pathname);
      return false;
    } else {
      window.location.hash = JSON.stringify(data);
      return true;
    }
  }

  static get() {
    try {
      const data = JSON.parse(decodeURI(window.location.hash.substring(1)) || "null");
      console.log(data);
      return data;
    } catch (e) {

    }
    return null;
  }
}
