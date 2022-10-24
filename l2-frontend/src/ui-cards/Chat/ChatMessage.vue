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
      v-if="message.type === 2"
      class="message-text message-file"
    >
      <div class="message-file-icon">
        <i class="fas fa-file" />
      </div>
      <a
        class="message-file-name a-under-reversed"
        download
        :href="message.file.url"
      >
        {{ message.file.name }}
      </a>
    </div>
    <div
      v-else-if="message.type === 3"
      class="message-text message-image"
    >
      <img
        v-img
        class="message-image-img"
        :src="message.file.url"
        :style="{ height: `${imageSmallHeight}px`, width: `${imageSmallWidth}px` }"
      >
    </div>
    <div
      v-else
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

<script lang="ts">
import { menuItems } from '@/pages/Stationar/mixins/menu';

const fixLinkUrl = url => {
  let anchor = url.split('#')[1];
  if (anchor) {
    if (anchor.includes(' ')) {
      anchor = anchor.replace(/ /g, '%20');
    }

    if (anchor === decodeURIComponent(anchor)) {
      anchor = encodeURIComponent(anchor);
    }
    return `${url.split('#')[0]}#${anchor}`;
  }
  return url;
};

const parseQueryString = (queryString): Record<string, string> => {
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

const markdownTextToHtml = str => {
  const codeMultiline = str.replace(/```([^`]+)```/g, '<code class="code-newline">$1</code>');
  const codeWithoutNewLine = codeMultiline.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  let codeFixed = codeWithoutNewLine.replace(/<code>\n/g, '<code>');
  codeFixed = codeFixed.replace(/<code class="code-newline">\n/g, '<code class="code-newline">');
  codeFixed = codeFixed.replace(/\n<\/code>/g, '</code>');

  const tagsAtPositions = [];
  const codeTagsReplaced = codeFixed.replace(/<code>([^<]+)<\/code>/g, (match, p1, offset) => {
    tagsAtPositions.push({ pos: offset, text: p1, tag: 'code' });
    return `$TAG_code_${offset}$`;
  });

  const links = codeTagsReplaced.replace(/(https?:\/\/\S+)/g, (match, url) => {
    const fixedUrl = fixLinkUrl(url);
    const fixedName = fixLinkName(url);
    return `<a href="${fixedUrl}" class="a-under" target="_blank">${fixedName}</a>`;
  });
  const aTagsReplacedWithAnyAttributes = links.replace(/<a([^>]+)>([^<]+)<\/a>/g, (match, p1, p2, offset) => {
    tagsAtPositions.push({
      pos: offset,
      text: p2,
      tag: 'a',
      attrs: p1,
    });
    return `$TAG_a_${offset}$`;
  });

  const bold = aTagsReplacedWithAnyAttributes.replace(/(?<!<code>)(\*\*([^*]+)\*\*)(?!<\/code>)/g, '<b>$2</b>');
  const italic = bold.replace(/(?<!<code>)(\*([^*]+)\*)(?!<\/code>)/g, '<i>$2</i>');
  const underline = italic.replace(/(?<!<code>)(__([^_]+)__)(?!<\/code>)/g, '<u>$2</u>');
  const strikethrough = underline.replace(/(?<!<code>)(~~([^~]+)~~)(?!<\/code>)/g, '<s>$2</s>');

  const nlToBr = strikethrough.replace(/\n/g, '<br />');

  const tagsRestored = tagsAtPositions.reduce(
    (acc, {
      pos, text, tag, attrs,
    }) => acc.replace(`$TAG_${tag}_${pos}$`, `<${tag}${attrs || ''}>${text}</${tag}>`),
    nlToBr,
  );
  return tagsRestored;
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
      // eslint-disable-next-line no-misleading-character-class
      let text = this.message.text.replace(/^[\u200B\u200C\u200D\u200E\u200F\uFEFF]/, '');
      text = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');

      text = markdownTextToHtml(text);

      return text;
    },
    imageSmallWidth() {
      return Math.min(this.message.imageDimensions.width || 1, 363);
    },
    imageSmallHeight() {
      if (this.message.type !== 3) {
        return 0;
      }

      const ratio = this.message.imageDimensions.width / this.imageSmallWidth;

      if (this.message.imageDimensions.width !== this.imageSmallWidth) {
        return Math.min(600, this.message.imageDimensions.height / ratio);
      }

      return Math.min(600, this.message.imageDimensions.height || 1);
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

  ::v-deep .code-newline {
    display: block;
    white-space: pre-wrap;
    word-break: break-word;
  }

  &-image img {
    max-height: 600px;
    max-width: 100%;
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    margin-bottom: 5px;
  }

  &-file {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 5px;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    cursor: pointer;

    &-icon {
      width: 30px;
      height: 30px;
      margin-right: 5px;
      line-height: 30px;
      text-align: center;
    }

    &-name {
      font-size: 14px;
      color: #333;
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
