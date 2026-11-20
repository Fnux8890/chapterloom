execute as @a[scores={col_found=1..}] at @s run function colonies:found
execute as @a[scores={col_join=1..}] at @s run function colonies:join
scoreboard players enable @a col_found
scoreboard players enable @a col_join
scoreboard players add #clock col_api 1
execute if score #clock col_api matches 20.. run function colonies:survey
