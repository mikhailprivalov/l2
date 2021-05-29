export interface Hr {
  hr: true,
}

export interface Button {
  url: string,
  title: string,
  nt: boolean | void,
  not_show_home: boolean | void,
}

export type MenuItem = Hr | Button;

export interface Menu {
  version: string;
  region: string;
  buttons: MenuItem[];
}
