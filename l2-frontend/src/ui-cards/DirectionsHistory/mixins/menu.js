const menuItems = Object.freeze({
  directions_list: {
    title: 'Создать список назначений',
    handler() {
      this.$root.$emit('print:directions_list', this.checked)
    },
  },
  copy_researches: {
    title: 'Скопировать исследования для назначения',
    onlyNotForIssledovaniye: true,
    handler() {
      for (let dir of this.directions) {
        if (this.in_checked(dir.pk)) {
          for (let pk of dir.researches_pks) {
            this.$root.$emit('researches-picker:add_research', pk)
          }
        }
      }
    },
  },
  print_results: {
    title: 'Печать результатов',
    handler() {
      this.$root.$emit('print:results', this.checked)
    },
  },
  print_barcodes: {
    title: 'Печать штрих-кодов',
    handler() {
      this.$root.$emit('print:barcodes', this.checked)
    },
  },
  print_directions: {
    title: 'Печать направлений',
    handler() {
      this.$root.$emit('print:directions', this.checked)
    },
  },
  change_parent: {
    title: 'Назначить главное направление',
    onlyForTypes: [3],
    handler() {
      if (this.checked.length > 3) {
        this.$dialog.alert({
            title: "Количество не может быть больше 3",
            okText: 'OK',
        })
      }
      else {
        this.change_parent_open = true
      }
    },
  },
})

export default {
  data() {
    return {
      menuItems,
    }
  }
}
