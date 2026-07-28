import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'registro',
    loadComponent: () =>
      import('./auth/registro/registro.component').then((m) => m.RegistroComponent),
  },
  {
    path: 'logout',
    loadComponent: () =>
      import('./auth/logout/logout.component').then((m) => m.LogoutComponent),
  },
  { path: 'oficina' },
  { path: 'taller' },
  { path: 'inventario' },
  { path: 'configuracion' },
];
