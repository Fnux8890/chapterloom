scoreboard players set @s col_join 0
execute unless entity @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] run return run tellraw @s {"text":"No colony charter within 12 blocks."}
scoreboard players operation @s col_id = @e[type=minecraft:marker,tag=col_charter,distance=..12,sort=nearest,limit=1] col_id
tellraw @s {"text":"Joined this colony. Build a bookshelf one block east of its lodestone, with a lectern on top."}
