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
  {
    title: 'Печать набора документов',
    handler() {
      this.$root.$emit('print:directions:appendix', this.checked);
    },
  },
  {
    title: 'Отправить результаты на email пациента',
    requiredModule: 'l2_send_patients_email_results',
    handler() {
      this.$root.$emit('directions:resend-patient-email-results', this.checked);
    },
  },
  {
    title: 'экспорт в docx',
    requiredModule: 'l2_docx_aggregate_laboratory_results',
    handler() {
      this.$root.$emit('print:aggregate_laboratory_results', this.checked);
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
