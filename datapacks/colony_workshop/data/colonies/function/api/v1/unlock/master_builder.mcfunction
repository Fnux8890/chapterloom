# Synchronous v1 query. A present provider always writes both the availability and unlock results.
function colonies:api/v1/query
scoreboard players set #unlocked col_api 0
execute if score #level col_api matches 2.. run scoreboard players set #unlocked col_api 1
