const menuItems = [
  {
    title: 'Создать список назначений',
    handler() {
      this.$root.$emit('print:directions_list', this.checked);
    },
  },
  {
    title: 'Скопировать исследования для назначения',
    onlyNotForIssledovaniye: true,
    handler() {
      for (const dir of this.directions) {
        if (this.in_checked(dir.pk)) {
          for (const pk of dir.researches_pks) {
            this.$root.$emit('researches-picker:add_research', pk);
          }
        }
      }
    },
  },
  {
    title: 'Печать результатов',
    handler() {
      this.$root.$emit('print:results', this.checked);
    },
  },
  {
    title: 'Печать штрих-кодов',
    handler() {
      this.$root.$emit('print:barcodes', this.checked);
    },
  },
  {
    title: 'Печать направлений',
    handler() {
      this.$root.$emit('print:directions', this.checked);
    },
  },
  {
    title: 'Назначить главное направление',
    onlyForTypes: [3],
    requiredGroup: 'Врач стационара',
    handler() {
      if (this.checked.length > 3) {
        this.$dialog.alert({
          title: 'Количество не может быть больше 3',
          okText: 'OK',
        });
      } else {
        this.isOpenChangeParent = true;
      }
    },
  },
];

export default {
  data() {
    return {
      menuItems,
    };
  },
};
