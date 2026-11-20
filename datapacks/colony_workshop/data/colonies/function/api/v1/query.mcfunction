# Run as the actor at the action site. Level zero means there is no matching local membership.
scoreboard players set #provider col_api 1
scoreboard players set #level col_api 0
execute unless entity @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] run return 0
execute unless score @s col_id = @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] col_id run return 0
execute as @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] at @s unless score @s col_level matches 2.. run function colonies:check_hut
scoreboard players operation #level col_api = @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] col_level
