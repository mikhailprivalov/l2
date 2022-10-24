import { smartCall } from './http-common';

export default (point: string, ctx?: any, pickKeys?: any, moreData?: any, formData?: FormData | null): any => smartCall({
  url: point, ctx, moreData, pickKeys, formData,
});
