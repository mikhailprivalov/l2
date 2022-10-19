export interface ChatsUser {
  id: number;
  name: string;
  isOnline: boolean;
  lastOnline: string | null;
  position: string | null;
  speciality: string | null;
}

export interface ChatsDepartment {
  id: number;
  title: string;
  usersOnline: number;
  users: ChatsUser[];
}
