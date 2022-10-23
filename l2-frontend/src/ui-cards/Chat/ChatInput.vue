<template>
  <div
    :id="uniqueId"
    class="input-wrapper"
  >
    <ResizeDetector
      :target="`#${uniqueId}`"
      observe-height
      @resize="onResize"
    />

    <div
      v-if="imageInfo"
      class="preview-image"
    >
      <div
        class="preview-image-wrapper"
        :style="{ backgroundImage: `url(${imageInfo.url})` }"
      />
      <div class="preview-image-info">
        <div class="preview-image-info-name">
          {{ imageInfo.name }}
        </div>
        <div class="preview-image-info-size">
          {{ imageInfo.size }}
        </div>
      </div>
      <div
        class="preview-image-remove"
        @click="imageClear"
      >
        <i class="fa fa-times" />
      </div>
    </div>
    <div
      v-else-if="fileInfo"
      class="preview-file"
    >
      <div class="preview-file-wrapper">
        <i
          class="fa"
          :class="`fa-${fileAttachedTypeByExtension}`"
        />
      </div>
      <div class="preview-file-info">
        <div class="preview-file-info-name">
          {{ fileInfo.name }}
        </div>
        <div class="preview-file-info-size">
          {{ fileInfo.size }}
        </div>
      </div>
      <div
        class="preview-file-remove"
        @click="fileClear"
      >
        <i class="fa fa-times" />
      </div>
    </div>
    <textarea
      v-else
      ref="input"
      v-model="text"
      v-autosize="text"
      class="input-textarea"
      :placeholder="
        selfDialog
          ? 'Введите сообщение для отправки себе'
          : 'Введите сообщение (Ctrl+Enter для отправки)'
      "
      :readonly="disabled"
      maxlength="999"
      @keydown.ctrl.enter="send"
    />
    <div
      v-if="!text && !disabled && !imageInfo && !fileInfo"
      class="input-attach"
      @mouseover="attachFileMenuOpen"
      @mouseleave="attachFileMenuHide"
    >
      <button class="btn btn-link">
        <i class="fa fa-paperclip" />
      </button>
      <div
        v-if="attachFileMenuOpened"
        class="input-attach-menu"
        :class="attachFileMenuDisplayed && 'input-attach-menu-opened'"
      >
        <div
          class="input-attach-menu-item"
          @click="attachFile"
        >
          <i class="fa fa-file" />
          <span>Прикрепить файл</span>
        </div>
        <div
          class="input-attach-menu-item"
          @click="attachImage"
        >
          <i class="fa fa-image" />
          <span>Прикрепить изображение</span>
        </div>
      </div>
    </div>
    <input
      ref="attachFile"
      type="file"
      class="input-attach-file"
      @change="attachFileChange"
    >
    <input
      ref="attachImage"
      type="file"
      class="input-attach-image"
      accept="image/*"
      @change="attachImageChange"
    >
  </div>
</template>

<script lang="ts">
import ResizeDetector from 'vue-resize-detector';

const fileSizeToString = (size: number) => {
  if (size < 1024) {
    return `${size} байт`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} Кб`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} Мб`;
};

const MAX_FILE_SIZE = 2 * 1024 * 1024;
const MAX_FILE_SIZE_STRING = fileSizeToString(MAX_FILE_SIZE);

export default {
  name: 'ChatInput',
  components: {
    ResizeDetector,
  },
  props: {
    selfDialog: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      uniqueId: `dialog-input-${Math.random().toString(36).substr(2, 9)}`,
      text: '',
      fileInfo: null,
      imageInfo: null,
      attachFileMenuOpened: false,
      attachFileMenuDisplayed: false,
    };
  },
  computed: {
    textSymbolsLeft() {
      return 999 - this.text.length;
    },
    fileAttachedTypeByExtension() {
      if (!this.fileInfo) {
        return null;
      }
      const extension = this.fileInfo.name.split('.').pop();
      if (extension === 'pdf') {
        return 'file-pdf';
      }
      if (extension === 'doc' || extension === 'docx') {
        return 'file-word';
      }
      if (extension === 'xls' || extension === 'xlsx') {
        return 'file-excel';
      }
      if (extension === 'ppt' || extension === 'pptx') {
        return 'file-powerpoint';
      }
      if (extension === 'zip' || extension === 'rar' || extension === '7z' || extension === 'gz' || extension === 'tar') {
        return 'file-zipper';
      }
      if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(extension)) {
        return 'file-image';
      }

      return 'file';
    },
  },
  watch: {
    text() {
      if (this.text) {
        if (this.textSymbolsLeft <= 0) {
          this.text = this.text.slice(0, 999);
        } else {
          this.$emit('typing');
        }
      }
    },
  },
  methods: {
    onResize() {
      this.$emit('resize');
    },
    send() {
      if (this.text || this.imageInfo || this.fileInfo) {
        this.$emit('send', {
          text: this.text,
          image: this.$refs.attachImage?.files ? this.$refs.attachImage.files[0] : null,
          file: this.$refs.attachFile?.files ? this.$refs.attachFile.files[0] : null,
        }, this.onResult);
      }
    },
    onResult(result: boolean) {
      if (result) {
        this.clear();
      }
      this.$nextTick(() => {
        this.focus();
      });
    },
    focus() {
      this.$refs.input?.focus();
    },
    clear() {
      this.text = '';
      this.imageClear();
      this.fileClear();
    },
    attachFileMenuOpen() {
      this.attachFileMenuOpened = true;
      setTimeout(() => {
        this.attachFileMenuDisplayed = true;
      }, 10);
    },
    attachFileMenuHide() {
      this.attachFileMenuDisplayed = false;
      setTimeout(() => {
        this.attachFileMenuOpened = false;
      }, 200);
    },
    attachFile() {
      this.$refs.attachFile.click();
      this.attachFileMenuHide();
    },
    attachImage() {
      this.$refs.attachImage.click();
      this.attachFileMenuHide();
    },
    attachImageChange(e: any) {
      const { files } = e.target;
      if (files?.length) {
        const file = files[0];

        if (file.size > MAX_FILE_SIZE) {
          this.$root.$emit('msg', 'error', `Максимальный размер изображения ${MAX_FILE_SIZE_STRING}`);
          e.target.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = (ev: any) => {
          this.imageInfo = {
            name: file.name,
            size: fileSizeToString(file.size),
            url: ev.target.result,
          };
        };
        reader.readAsDataURL(file);
      } else {
        this.imageClear();
      }
    },
    attachFileChange(e: any) {
      const { files } = e.target;
      if (files?.length) {
        const file = files[0];
        if (file.size > MAX_FILE_SIZE) {
          this.$root.$emit('msg', 'error', `Максимальный размер файла ${MAX_FILE_SIZE_STRING}`);
          e.target.value = '';
          return;
        }
        this.fileInfo = {
          name: file.name,
          size: fileSizeToString(file.size),
        };
      } else {
        this.fileClear();
      }
    },
    imageClear() {
      this.imageInfo = null;
      this.$refs.attachImage.value = '';
    },
    fileClear() {
      this.fileInfo = null;
      this.$refs.attachFile.value = '';
    },
  },
};
</script>

<style lang="scss" scoped>
.input-wrapper {
  position: relative;
}

.input-textarea {
  display: block;
  width: 100%;
  min-height: 40px;
  max-height: 120px;
  padding: 5px;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.1;
}

.preview-image {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  height: 120px;
  background-color: #f5f5f5;
  overflow: hidden;
  padding: 10px;

  &-remove {
    position: absolute;
    top: 5px;
    left: 135px;
    cursor: pointer;
  }

  &-wrapper {
    position: relative;
    width: 120px;
    height: 100%;
    overflow: hidden;
    background-position: center;
    background-repeat: no-repeat;
    background-size: contain;
  }

  &-info {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: calc(100% - 150px);
    height: 100%;
    padding: 0 10px 0 20px;
    box-sizing: border-box;
    word-break: break-all;

    &-name {
      font-size: 13px;
      line-height: 1.2;
      max-height: 100px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.preview-file {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 40px;
  padding: 5px;
  margin-bottom: 5px;
  background-color: #f5f5f5;
  border-radius: 5px;
  overflow: hidden;

  &-remove {
    position: absolute;
    top: 5px;
    left: 35px;
    cursor: pointer;
  }

  &-info {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: calc(100% - 40px);
    height: 100%;
    padding: 0 10px;
    box-sizing: border-box;
    word-break: break-all;

    &-name {
      font-size: 13px;
      line-height: 1.2;
      max-height: 100px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  &-wrapper {
    width: 30px;
    text-align: center;
  }
}

.input-attach {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &-file, &-image {
    display: none;
  }

  .btn {
    padding: 0;
    margin: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: transparent;
    border: none;
    outline: none;
    cursor: pointer;

    .fa {
      font-size: 20px;
    }
  }

  .btn-link {
    color: #8c8c8c;

    &:hover {
      color: #494949;
      text-decoration: none;
    }
  }

  .input-attach-menu {
    position: absolute;
    bottom: 100%;
    right: 0;
    z-index: 1001;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    padding: 5px 0;
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: 3px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
    cursor: default;
    opacity: 0;
    transition: opacity 0.2s ease-in-out;

    &-opened {
      opacity: 1;
    }

    .input-attach-menu-item {
      display: flex;
      align-items: center;
      padding: 5px 10px;
      font-size: 14px;
      color: #333;
      cursor: pointer;

      &:hover {
        background-color: #f5f5f5;
      }

      .fa {
        margin-right: 5px;
        width: 18px;
        text-align: center;
      }
    }
  }
}
</style>
