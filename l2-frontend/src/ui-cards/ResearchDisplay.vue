<template>
  <div class="root-c" @click.left="remove" @click.right.prevent="update_comment">
    <div class="root-in">{{title}}<span class="comment" v-if="comment !== '' && !simple">[{{comment}}]</span></div>
    <div v-if="n + 1 < nof" class="root-div"></div>
  </div>
</template>

<script>
  export default {
    name: 'research-display',
    props: {
      title: {
        type: String,
      },
      n: {
        type: Number,
      },
      nof: {
        type: Number,
      },
      pk: {
        type: Number
      },
      comment: {
        type: String,
        default: ''
      },
      simple: {
        type: Boolean,
        default: false,
      }
    },
    methods: {
      remove() {
        this.$root.$emit('researches-picker:deselect', this.pk)
      },
      update_comment() {
        if (this.simple)
          return
        this.$root.$emit('researches-picker:update-comment', this.pk)
      }
    }
  }
</script>

<style scoped>
  .root-c {
    display: inline-block;
    white-space: nowrap;
  }

  .root-in, .root-div {
    display: inline-block;
  }

  .root-in {
    padding: 3px;
    cursor: pointer;
    border: 1px solid transparent;
    font-size: 12px;
  }

  .root-in:hover {
    background-color: #eee;
    border-color: #bbb;
  }

  .root-div {
    width: 1px;
    height: 15px;
    background-color: #000;
    margin-bottom: -3px;
    margin-left: -1px;
    margin-right: 3px;
  }

  .comment {
    margin-left: 3px;
    color: #049372;
    font-weight: 600;
  }
</style>
