#!/bin/bash
# Batch generation for all hassaku-teasing themes
# Generates 3 styles (default, teasing, sexy) × 20 images per theme

cd /mnt/d/StableDiffusion/private-new

TEMPLATE="./prompts/hassaku-teasing/teasing-themable-v2.prompt.yaml"

# Build session list (theme:style:count format)
../local-sd-generator/tools/batch_generate.sh -t "$TEMPLATE" \
   adepta_sororitas:default:10 \
   adepta_sororitas:teasing:10 \
   adepta_sororitas:sexy:10 \
   dark_fantasy:default:10 \
   dark_fantasy:teasing:10 \
   dark_fantasy:sexy:10


#  adepta_sororitas:default:20 adepta_sororitas:teasing:20 adepta_sororitas:sexy:20 \
#  annees_folles:default:20 annees_folles:teasing:20 annees_folles:sexy:20 \
#  antiquite:default:20 antiquite:teasing:20 antiquite:sexy:20 \
#  arabesque:default:20 arabesque:teasing:20 arabesque:sexy:20 \
#  burlesque:default:20 burlesque:teasing:20 burlesque:sexy:20 \
#  business:default:20 business:teasing:20 business:sexy:20 \
#  campus:default:20 campus:teasing:20 campus:sexy:20 \
#  cheerleader:default:20 cheerleader:teasing:20 cheerleader:sexy:20 \
#  chine_medievale:default:20 chine_medievale:teasing:20 chine_medievale:sexy:20 \
#  cirque:default:20 cirque:teasing:20 cirque:sexy:20 \
#  cosmic_horror:default:20 cosmic_horror:teasing:20 cosmic_horror:sexy:20 \
#  cyberpunk:default:20 cyberpunk:teasing:20 cyberpunk:sexy:20 \
#  cyber_bright:default:20 cyber_bright:teasing:20 cyber_bright:sexy:20 \
#  disco:default:20 disco:teasing:20 disco:sexy:20 \
#  fantasy:default:20 fantasy:teasing:20 fantasy:sexy:20 \
#  fetish:default:20 fetish:teasing:20 fetish:sexy:20 \
#  gala:default:20 gala:teasing:20 gala:sexy:20 \
#  gothic_lolita:default:20 gothic_lolita:teasing:20 gothic_lolita:sexy:20 \
#  gym-trainer:default:20 gym-trainer:teasing:20 gym-trainer:sexy:20 \
#  hotesse:default:20 hotesse:teasing:20 hotesse:sexy:20 \
#  japon_medieval:default:20 japon_medieval:teasing:20 japon_medieval:sexy:20 \
#  librarian:default:20 librarian:teasing:20 librarian:sexy:20 \
#  lifeguard:default:20 lifeguard:teasing:20 lifeguard:sexy:20 \
#  lifestyle:default:20 lifestyle:teasing:20 lifestyle:sexy:20 \
#  mafia_1920:default:20 mafia_1920:teasing:20 mafia_1920:sexy:20 \
#  maid:default:20 maid:teasing:20 maid:sexy:20 \
#  medical:default:20 medical:teasing:20 medical:sexy:20 \
#  monster_girls:default:20 monster_girls:teasing:20 monster_girls:sexy:20 \
#  motarde:default:20 motarde:teasing:20 motarde:sexy:20 \
#  moyen_age:default:20 moyen_age:teasing:20 moyen_age:sexy:20 \
#  nightclub:default:20 nightclub:teasing:20 nightclub:sexy:20 \
#  noir:default:20 noir:teasing:20 noir:sexy:20 \
#  pinup:default:20 pinup:teasing:20 pinup:sexy:20 \
#  pirates:default:20 pirates:teasing:20 pirates:sexy:20 \
#  policiere:default:20 policiere:teasing:20 policiere:sexy:20 \
#  post_apo:default:20 post_apo:teasing:20 post_apo:sexy:20 \
#  renaissance:default:20 renaissance:teasing:20 renaissance:sexy:20 \
#  rockstar:default:20 rockstar:teasing:20 rockstar:sexy:20 \
#  schoolgirl:default:20 schoolgirl:teasing:20 schoolgirl:sexy:20 \
#  secretary:default:20 secretary:teasing:20 secretary:sexy:20 \
#  space_opera:default:20 space_opera:teasing:20 space_opera:sexy:20 \
#  sport:default:20 sport:teasing:20 sport:sexy:20 \
#  steampunk:default:20 steampunk:teasing:20 steampunk:sexy:20 \
#  streetwear:default:20 streetwear:teasing:20 streetwear:sexy:20 \
#  tropical:default:20 tropical:teasing:20 tropical:sexy:20 \
#  victorien:default:20 victorien:teasing:20 victorien:sexy:20 \
#  waitress:default:20 waitress:teasing:20 waitress:sexy:20 \
#  yoga-instructor:default:20 yoga-instructor:teasing:20 yoga-instructor:sexy:20
