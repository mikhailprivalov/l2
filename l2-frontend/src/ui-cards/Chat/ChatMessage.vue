<template>
  <div
    class="message"
    :class="newMessages.includes(message.id) && 'message-new'"
  >
    <div
      class="message-author"
      :class="message.author === currentUserPk && 'message-author-current-user'"
    >
      {{ message.author === currentUserPk ? 'Вы' : dialogUserObj.name }}
    </div>
    <div
      class="message-text"
      v-html=" /* eslint-disable-line */ htmlText"
    />
    <div
      class="message-time"
    >
      <i
        v-if="message.read"
        class="fa fa-check-double message-time-read"
      />
      <i
        v-else
        class="fa fa-check message-time-unread"
      />
      {{ message.time | unixTimestampToLocalFormattedTime }}
    </div>
    <div
      v-tippy
      class="message-copy"
      title="Скопировать сообщение"
      @click="copyText"
    >
      <i class="fa fa-copy" />
    </div>
  </div>
</template>

<script>
import { menuItems } from '@/pages/Stationar/mixins/menu';

const fixLinkUrl = url => {
  const anchor = url.split('#')[1];
  if (anchor) {
    return `${url.split('#')[0]}#${encodeURIComponent(anchor.replace('%20', ' '))}`;
  }
  return url;
};

const parseQueryString = (queryString) => {
  const query = {};
  const pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
  for (let i = 0; i < pairs.length; i += 1) {
    const pair = pairs[i].split('=');
    query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
  }
  return query;
};

const fixLinkName = url => {
  if (url.indexOf(window.location.origin) === -1) {
    return url;
  }

  const urlWithoutProtocol = url.replace(/(^\w+:|^)\/\//, '');
  const [, ...urlWithoutHost] = urlWithoutProtocol.split('/');
  const r = urlWithoutHost.join('/');

  if (r === 'ui/directions') {
    return 'Страница направлений';
  }

  if (r.startsWith('ui/results/preview?') || r.startsWith('results/pdf?')) {
    // parse json array from pk query
    const [, q] = r.split('?');
    const query = parseQueryString(q);

    if (query.pk) {
      try {
        const pk = JSON.parse(query.pk);
        if (pk.length === 1) {
          return `PDF результат №${pk[0]}`;
        }
        return `PDF результаты ${pk.map(p => `№${p}`).join(', ')}`;
      } catch (e) {
        // ignore
      }
    }
  } else if (r.startsWith('ui/stationar#')) {
    const [, a] = r.split('#');
    const anchor = decodeURIComponent(a);
    try {
      const anchorObj = JSON.parse(anchor);
      if (anchorObj.pk) {
        let t = `Стационар, И/б №${anchorObj.pk}`;

        if (anchorObj.every) {
          t += ' - полная история';
        }

        if (anchorObj.opened_list_key && menuItems[anchorObj.opened_list_key]) {
          t += `: ${menuItems[anchorObj.opened_list_key]}`;
        }

        if (anchorObj.opened_form_pk) {
          t += ` - форма №${anchorObj.opened_form_pk}`;
        }

        return t;
      }
    } catch (e) {
      // ignore
    }
  }

  return r;
};

export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      required: true,
    },
    dialogUserObj: {
      type: Object,
      required: true,
    },
    newMessages: {
      type: Array,
      required: true,
    },
  },
  computed: {
    currentUserPk() {
      return this.$store.getters.currentDocPk;
    },
    htmlText() {
      let text = this.message.text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      // eslint-disable-next-line no-misleading-character-class
      text = text.replace(/^[\u200B\u200C\u200D\u200E\u200F\uFEFF]/, '');

      text = text.replace(/(https?:\/\/\S+)/g, (match, url) => {
        const fixedUrl = fixLinkUrl(url);
        const fixedName = fixLinkName(url);
        return `<a href="${fixedUrl}" class="a-under" target="_blank">${fixedName}</a>`;
      });

      text = text.replace(/(\n)/g, '<br />');

      return text;
    },
  },
  methods: {
    copyText() {
      const el = document.createElement('textarea');
      el.value = this.message.text;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      this.$root.$emit('msg', 'ok', 'Сообщение скопировано');
    },
  },
};
</script>

<style scoped lang="scss">
.message {
  position: relative;
  padding: 5px 5px 16px 10px;
  border-top: 1px solid #ccc;

  &-new {
    background-color: #ecfdff;
  }

  &-text {
    font-size: 14px;
    padding-left: 5px;
    word-break: break-word;
  }

  &-author {
    font-weight: 700;
    color: #333333;
  }

  &e-author-current-user {
    color: #888888;
  }

  &-time {
    position: absolute;
    bottom: 2px;
    right: 19px;
    font-size: 12px;

    &-read {
      color: #4caf50;
    }

    &-unread {
      color: #999;
    }
  }
}

.message-copy {
  position: absolute;
  bottom: -1px;
  right: 2px;
  cursor: pointer;
  color: #dbdbdb;

  &:hover {
    color: #333;
  }
}
</style>
