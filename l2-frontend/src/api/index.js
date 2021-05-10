import { smartCall } from '@/api/http-common';

export default (point, ctx, pickKeys, moreData) => smartCall({
  url: point, ctx, moreData, pickKeys,
});
