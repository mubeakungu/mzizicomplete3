import Phaser from 'phaser';

import CONFIG from '../../config/game';
import GameScene from '../game/GameScene';

/**
 * Boot game scene
 * @class BootScene
 * @extends {Phaser.Scene}
 */
class BootScene extends Phaser.Scene {
  static CONFIG = CONFIG.SCENES.BOOT;

  /**
   * Creates an instance of BootScene
   */
  constructor() {
    super(BootScene.CONFIG.NAME);
  }

  preload() {
    // Assets are served under Vite's configured base path (/games/ in this
    // deployment) — hardcoding a root-absolute path 404s once the app is
    // mounted anywhere other than the domain root.
    const base = import.meta.env.BASE_URL; // e.g. '/games/'
    this.load.atlas('dino', `${base}dino-assets/sprites/dino-atlas.png`, `${base}dino-assets/sprites/dino-atlas.json`);

    this.load.bitmapFont(
      'joystix',
      `${base}dino-assets/fonts/joystix_monospace.png`,
      `${base}dino-assets/fonts/joystix_monospace.fnt`,
    );

    this.load.audio('player-action', `${base}dino-assets/sounds/player-action.mp3`);
    this.load.audio('achievement', `${base}dino-assets/sounds/achievement.mp3`);
    this.load.audio('gameover', `${base}dino-assets/sounds/gameover.mp3`);
  }

  create() {
    this.scene.start(GameScene.CONFIG.NAME);
  }
}

export default BootScene;
