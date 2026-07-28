import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { LogoutComponent } from './logout.component';
import { AuthTokenService, } from '../auth-token.service';

describe('LogoutComponent', () => {
  let tokenService: AuthTokenService;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [LogoutComponent],
      providers: [provideRouter([])],
    }).compileComponents();
    tokenService = TestBed.inject(AuthTokenService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('borra el token y redirige a /login al inicializarse', () => {
    tokenService.setToken('token-activo');
    const navigateSpy = spyOn(router, 'navigate');

    const fixture = TestBed.createComponent(LogoutComponent);
    fixture.detectChanges();

    expect(tokenService.getToken()).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });
});
