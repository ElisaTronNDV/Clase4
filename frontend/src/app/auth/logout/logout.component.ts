import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';

import { AuthTokenService } from '../auth-token.service';

@Component({
  selector: 'app-logout',
  standalone: true,
  template: '',
})
export class LogoutComponent implements OnInit {
  private readonly tokenService = inject(AuthTokenService);
  private readonly router = inject(Router);

  ngOnInit(): void {
    this.tokenService.clearToken();
    this.router.navigate(['/login']);
  }
}
