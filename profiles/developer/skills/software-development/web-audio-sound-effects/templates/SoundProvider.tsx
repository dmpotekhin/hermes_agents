// Центральная маршрутизация socket-событий → звуки.
// Сопоставь свои события в useSocketEvent(...) с именами из SoundName.
import { useEffect, useSyncExternalStore, type ReactNode } from 'react';
import { useSocketEvent } from './socket';
import { isMuted, play, subscribe, toggleMuted, unlock } from './sound';

export function SoundProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const unlockOnce = () => unlock();
    window.addEventListener('pointerdown', unlockOnce);
    window.addEventListener('keydown', unlockOnce);
    return () => {
      window.removeEventListener('pointerdown', unlockOnce);
      window.removeEventListener('keydown', unlockOnce);
    };
  }, []);

  // Сервер шлёт событие всем в комнате (включая инициатора) — звук слышат ВСЕ.
  useSocketEvent('diceRolled', () => play('dice'));
  useSocketEvent('wheelSpinResult', () => play('wheelLand'));
  useSocketEvent('tarotDrawn', () => play('cardFlip'));
  useSocketEvent('icebreakerSelected', () => play('reveal'));
  useSocketEvent('matrixUpdated', () => play('tick'));

  return <>{children}</>;
}

// Хук для тумблера громкости. useSyncExternalStore — реактивность без контекста.
export function useMuted(): [boolean, () => void] {
  const muted = useSyncExternalStore(subscribe, isMuted);
  return [muted, toggleMuted];
}
