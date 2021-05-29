import { smartCall } from './http-common';

export default (point: string, ctx?: any, pickKeys?: any, moreData?: any): any => smartCall({
  url: point, ctx, moreData, pickKeys,
});
