scoreboard players set @s col_found 0
execute unless block ~ ~-1 ~ minecraft:lodestone run return run tellraw @s {"text":"Stand on a lodestone to found a colony."}
execute if entity @e[type=minecraft:marker,tag=col_charter,distance=..32] run return run tellraw @s {"text":"A charter is already nearby. Use /trigger col_join to join it."}
execute if score #last col_id matches 2147483647 run return 0
scoreboard players add #last col_id 1
execute align xyz positioned ~0.5 ~ ~0.5 summon minecraft:marker run function colonies:init_charter
function colonies:join
