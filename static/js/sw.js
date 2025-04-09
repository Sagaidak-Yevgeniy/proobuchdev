/**
 * Service Worker для обработки push-уведомлений
 */

// Версия Service Worker для кэширования
const CACHE_VERSION = 'v1';
const CACHE_NAME = `educational-platform-${CACHE_VERSION}`;

// Список URL, которые будем кэшировать
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/js/notifications.js',
  '/static/images/logo.png'
];

/**
 * Обработчик события установки Service Worker
 */
self.addEventListener('install', event => {
  console.log('Service Worker установлен');
  
  // Предварительно кэшируем файлы
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Открыт кэш');
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
        console.error('Ошибка при кэшировании файлов:', error);
      })
  );

  // Принудительно активируем Service Worker сразу после установки
  self.skipWaiting();
});

/**
 * Обработчик события активации Service Worker
 */
self.addEventListener('activate', event => {
  console.log('Service Worker активирован');

  // Очищаем старые версии кэша
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Удаляем старый кэш:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  // Захватываем контроль над всеми клиентами
  return self.clients.claim();
});

/**
 * Обработчик события fetch для перехвата запросов
 */
self.addEventListener('fetch', event => {
  // Не перехватываем запросы к API
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/admin/')) {
    return;
  }

  // Стратегия "сначала сеть, потом кэш"
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Если получили ответ от сети, кэшируем его
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Если сеть недоступна, пробуем взять из кэша
        return caches.match(event.request)
          .then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Можно вернуть заглушку для офлайн-режима
            // return caches.match('/offline.html');
          });
      })
  );
});

/**
 * Обработчик события push для получения push-уведомлений
 */
self.addEventListener('push', event => {
  console.log('[Service Worker] Получено push-уведомление');

  let notificationData = {};
  
  try {
    if (event.data) {
      notificationData = event.data.json();
    }
  } catch (e) {
    console.error('Ошибка при обработке данных уведомления:', e);
    
    // Используем значения по умолчанию, если не удалось получить данные
    notificationData = {
      title: 'Новое уведомление',
      body: 'У вас новое уведомление на платформе',
      icon: '/static/images/logo.png'
    };
  }
  
  // Настройки уведомления
  const notificationOptions = {
    body: notificationData.body || 'Содержание уведомления',
    icon: notificationData.icon || '/static/images/logo.png',
    badge: notificationData.badge || '/static/images/badge.png',
    tag: notificationData.tag || 'notification',
    data: {
      url: notificationData.url || '/'
    },
    vibrate: [100, 50, 100],
    requireInteraction: notificationData.requireInteraction || false,
    renotify: notificationData.renotify || false
  };

  // Показываем уведомление
  event.waitUntil(
    self.registration.showNotification(
      notificationData.title || 'Уведомление',
      notificationOptions
    )
  );
});

/**
 * Обработчик события клика по уведомлению
 */
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Клик по уведомлению');
  
  // Закрываем уведомление
  event.notification.close();
  
  // Получаем URL из данных уведомления
  const url = event.notification.data && event.notification.data.url 
    ? event.notification.data.url 
    : '/';
  
  // Открываем приложение и переходим по указанному URL
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then(clientList => {
        // Проверяем, есть ли уже открытые вкладки
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            // Если есть открытая вкладка, фокусируемся на ней и меняем URL
            return client.focus().then(() => {
              if (url) client.navigate(url);
            });
          }
        }
        
        // Если нет открытых вкладок, открываем новую
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
      .catch(error => {
        console.error('Ошибка при обработке клика по уведомлению:', error);
      })
  );
});

/**
 * Обработчик события закрытия уведомления
 */
self.addEventListener('notificationclose', event => {
  console.log('[Service Worker] Уведомление закрыто пользователем');
});