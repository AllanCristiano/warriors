# Guerreiros do Reino

Jogo 2D de ação/plataforma medieval feito em Godot 4.7. Escolha um guerreiro e
liberte o reino das hordas goblins, do Minotauro e de Cérbero.

## Como jogar
Abra o projeto no Godot (`project.godot`) e aperte F5.

| Ação      | Teclado            | Controle |
|-----------|--------------------|----------|
| Mover     | A / D ou setas     | D-pad / analógico |
| Pular     | Espaço ou K        | A |
| Atacar    | J ou Z             | X |
| Especial  | L ou X             | Y |
| Pausa     | Esc ou P           | Start |

### Guerreiros
- **Sir Aldric (Cavaleiro)**: equilibrado. Especial *Investida Real* (avança atravessando inimigos, invulnerável).
- **Brakka (Bárbaro)**: muita vida e força, lento. Especial *Terremoto* (dano em área).
- **Mestre Liang (Sábio Marcial)**: ataca à distância com dardos, pulo duplo. Especial *Leque de Dardos*.

### Fases
1. **Aldeia em Chamas**: noite de lua de sangue, casas incendiadas, brasas no ar, fosso com água e espinhos. Chefe: *Grukk, o General Goblin*.
2. **Muralhas de Pedraforte**: tempestade com chuva e relâmpagos, ponte levadiça, torres, escadarias de pedra, fossos. Chefe: *Tauron, o Minotauro*.
3. **Masmorras do Trono**: escuridão com tochas, rios de lava, corredor de espinhos, sala do trono. Chefe final: *Cérbero*.

## Estrutura
- `scenes/levels/level_N.tscn`: as fases. Tudo é editável no editor: blocos de terreno (`Terrain`, ajuste `size`/`style`),
  plataformas, props, inimigos (`Enemy`, troque `kind`), bandeiras de checkpoint, perigos, arena do chefe e saída.
- `scripts/`: herói, inimigos/chefes, projéteis, HUD, menus.
- `assets/sprites/`: spritesheets dos personagens já cortadas e alinhadas (geradas das pastas originais).
- `assets/kingdom/`: assets do reino (cenários, tiles, casas, torres, estandartes, UI) gerados proceduralmente.
- `assets/audio/`: efeitos e músicas medievais sintetizados, mais os sons originais do Cérbero.

## Ferramentas (pasta `tools/`, ignorada pelo Godot)
- `python tools/process_sprites.py`: recorta as spritesheets originais para `assets/sprites`.
- `python tools/gen_anims.py`: gera as animações que faltavam nas spritesheets (ataque/investida/pulo/dano/morte do
  cavaleiro, andar do sábio, mortes e dano de goblins, minotauro e Cérbero...). Rode depois de `process_sprites.py`.
- `python tools/gen_kingdom.py`: regenera os assets do reino (tema sombrio).
- `python tools/gen_audio.py`: regenera sons e músicas.
- `python tools/build_levels.py`: regenera as 3 fases a partir do design em código.
  **Atenção:** isso sobrescreve edições feitas nas fases pelo editor.

As pastas originais dos personagens têm um `.gdignore` para o Godot não importar as
spritesheets gigantes (ele usa as versões otimizadas em `assets/sprites`).
