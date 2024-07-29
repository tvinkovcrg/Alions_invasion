import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """Загальний клас, що керує ресурсам та поведінкою гри"""

    def __init__(self):
        """Ініціалізувати гру, створити ресурси гри"""
        pygame.init()

        self.settings = Settings()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption('Alien Invasion')

        self.stats = GameStats(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        self.play_button = Button(self, "Play")

    def run_game(self):
        """Розпочати головний цикл гри"""
        while True:
            # Слідкувати за подіями миші та клавіатури
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()

    def _check_events(self):
        """Реагувати на натискання клавіш та події миші"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Розпочати нову гру коли користувач натисне кнопку 'Play'"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # Recreate game statistic
            self.stats.reset_stats()
            self.stats.game_active = True

            # Delete aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            # Create new fleet and center ship
            self._create_fleet()
            self.ship.center_ship()

            # Hide the mouse cursor
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Реагування на натискання клавіш"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """Реагування на відпускання клавіш"""
        # Припиняємо переміщення корабля при відпусканні клавіші
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Створити нову кулю та додати її до групи куль"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Оновити позицію куль та позбавитися старих куль"""
        # Оновити позиції куль
        self.bullets.update()

        # Позбавлятися куль що зникли
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Реакція на зіткнення з прибульцями"""
        # Видалити всі кулі та прибульців що зіткнулися
        collision = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if not self.aliens:
            # Знищити наявні кулі та створити новий флот
            self.bullets.empty()
            self._create_fleet()

    def _update_aliens(self):
        """
        Перевірити чи флот знаходиться на краю,
        тоді оновити позиції всіх прибульців флоту
        """
        self._check_fleet_edges()
        self.aliens.update()

        # Шукати зіткнення куль із прибульцями
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Шукати чи котрийсь прибулець досяг низу екрану
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        """Перевірити чи не досяг якийсь прибулець нижнього краю екрану"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Зреагувати так ніби корабель було підбито
                self._ship_hit()
                break

    def _ship_hit(self):
        """Реагувати на зіткнення прибульців з кораблем"""
        if self.stats.ship_left > 0:
            # Зменшити ship_left
            self.stats.ship_left -= 1

            # delete bullets and aliens
            self.aliens.empty()
            self.bullets.empty()

            # create new fleet and respawn ship
            self._create_fleet()
            self.ship.center_ship()

            # Pause
            sleep(0.5)
        else:
            self.stats.game_active = False
            print('Ship dead')
            pygame.mouse.set_visible(True)

    def _check_fleet_edges(self):
        """
        Реагує відповідно до того, чи досяг
        котрийсь з прибульців карю екрана
        """
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Спуск всього флоту та зміна його напрямку"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _create_fleet(self):
        """Створити флот прибульців"""
        # Створити прибульців та визначити кількість прибульців у ряду
        # Відстань між прибульцями дорівнює ширині одного прибульця
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        avaible_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = avaible_space_x // (2 * alien_width)

        # Визначити, яка кількість рядів прибульців поміщається на екрані
        ship_height = self.ship.rect.height
        avaible_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        nuber_rows = avaible_space_y // (2 * alien_height)

        # Створити повний флот прибульців
        for row_number in range(nuber_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """Створити прибульця та поставити його до ряду"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _update_screen(self):
        """Оновити зображення на екрані та перемкнутися на новий екран"""
        # Наново перемалювати екран на кожній ітерації циклу
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # Намалювати кнопку 'Play' якщо гра неактивна
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':
    # Створити екземпляр гри та запустити гру
    ai = AlienInvasion()
    ai.run_game()
