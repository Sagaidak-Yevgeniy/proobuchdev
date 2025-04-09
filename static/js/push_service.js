/**
 * Push уведомления - сервис для работы с push уведомлениями
 */
class PushService {
    constructor() {
        this.swRegistration = null;
        this.isSubscribed = false;
        this.applicationServerPublicKey = null;
        this.apiBasePath = '/notifications/api';
    }

    /**
     * Инициализация сервиса
     */
    init() {
        // Проверяем, поддерживает ли браузер Service Worker и Push
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push notifications не поддерживаются этим браузером');
            return false;
        }

        // Регистрируем service worker
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('Service Worker зарегистрирован:', registration);
                this.swRegistration = registration;
                
                // Проверяем существующую подписку
                this.checkSubscription();
            })
            .catch(error => {
                console.error('Ошибка при регистрации Service Worker:', error);
            });
            
        return true;
    }

    /**
     * Проверяет активную подписку
     */
    checkSubscription() {
        if (!this.swRegistration) return;
        
        this.swRegistration.pushManager.getSubscription()
            .then(subscription => {
                this.isSubscribed = !(subscription === null);
                
                if (this.isSubscribed) {
                    console.log('Пользователь подписан на push-уведомления');
                    // Можно добавить визуальное отображение статуса подписки
                    this.sendSubscriptionToServer(subscription);
                } else {
                    console.log('Пользователь не подписан на push-уведомления');
                }
            })
            .catch(error => {
                console.error('Ошибка при проверке подписки:', error);
            });
    }

    /**
     * Запрашивает разрешение и подписывает пользователя на push-уведомления
     */
    subscribe() {
        if (!this.swRegistration) {
            console.error('Service Worker не зарегистрирован');
            return;
        }
        
        // Получаем публичный ключ с сервера
        this.getPublicKey()
            .then(publicKey => {
                const applicationServerKey = this.urlB64ToUint8Array(publicKey);
                
                // Запрашиваем разрешение и подписываем
                return this.swRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                });
            })
            .then(subscription => {
                console.log('Пользователь подписан на push-уведомления');
                this.isSubscribed = true;
                
                // Отправляем информацию о подписке на сервер
                this.sendSubscriptionToServer(subscription);
            })
            .catch(error => {
                console.error('Не удалось подписаться на push-уведомления:', error);
                // Если пользователь отклонил запрос разрешения
                if (Notification.permission === 'denied') {
                    console.warn('Пользователь отклонил разрешение на уведомления');
                }
            });
    }

    /**
     * Отменяет подписку на push-уведомления
     */
    unsubscribe() {
        if (!this.swRegistration) {
            console.error('Service Worker не зарегистрирован');
            return;
        }
        
        this.swRegistration.pushManager.getSubscription()
            .then(subscription => {
                if (!subscription) {
                    this.isSubscribed = false;
                    return;
                }
                
                // Сохраняем информацию перед отменой подписки
                const subscriptionInfo = {
                    endpoint: subscription.endpoint
                };
                
                // Отменяем подписку
                return subscription.unsubscribe()
                    .then(() => {
                        console.log('Подписка отменена');
                        this.isSubscribed = false;
                        
                        // Уведомляем сервер об отмене подписки
                        this.removeSubscriptionFromServer(subscriptionInfo);
                    });
            })
            .catch(error => {
                console.error('Ошибка при отмене подписки:', error);
            });
    }

    /**
     * Отправляет информацию о подписке на сервер
     */
    sendSubscriptionToServer(subscription) {
        if (!subscription) return;
        
        const browser = this.detectBrowser();
        const subscriptionJson = subscription.toJSON();
        
        // Формируем данные для отправки
        const data = {
            token: subscriptionJson.endpoint,
            device_type: 'web',
            device_name: browser,
            keys: subscriptionJson.keys
        };
        
        // Отправляем на сервер
        fetch(`${this.apiBasePath}/register-device/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Подписка успешно сохранена на сервере:', data);
            } else {
                console.error('Ошибка при сохранении подписки:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка при отправке подписки на сервер:', error);
        });
    }

    /**
     * Уведомляет сервер об отмене подписки
     */
    removeSubscriptionFromServer(subscriptionInfo) {
        fetch(`${this.apiBasePath}/remove-device/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                token: subscriptionInfo.endpoint
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Подписка успешно удалена на сервере:', data);
            } else {
                console.error('Ошибка при удалении подписки:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка при отправке запроса на удаление подписки:', error);
        });
    }

    /**
     * Получает публичный ключ VAPID с сервера
     */
    getPublicKey() {
        // Получаем публичный ключ для шифрования с сервера
        return fetch(`${this.apiBasePath}/get-public-key/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.publicKey) {
                    return data.publicKey;
                } else {
                    throw new Error('Не удалось получить публичный ключ');
                }
            });
    }

    /**
     * Преобразует строку в кодировке base64 в Uint8Array для использования в Web Push API
     */
    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }

    /**
     * Определяет браузер пользователя
     */
    detectBrowser() {
        const userAgent = navigator.userAgent;
        let browserName = 'Веб-браузер';
        
        if (userAgent.indexOf('Firefox') > -1) {
            browserName = 'Firefox';
        } else if (userAgent.indexOf('Chrome') > -1) {
            browserName = 'Chrome';
        } else if (userAgent.indexOf('Safari') > -1) {
            browserName = 'Safari';
        } else if (userAgent.indexOf('Edge') > -1 || userAgent.indexOf('Edg') > -1) {
            browserName = 'Edge';
        } else if (userAgent.indexOf('Opera') > -1 || userAgent.indexOf('OPR') > -1) {
            browserName = 'Opera';
        }
        
        return browserName;
    }

    /**
     * Получает CSRF-токен из куки
     */
    getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return this.getCookie('csrftoken');
    }

    /**
     * Получает значение cookie по имени
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Создаем и экспортируем экземпляр сервиса
const pushService = new PushService();
export default pushService;