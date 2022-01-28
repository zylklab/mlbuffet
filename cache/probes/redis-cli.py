import redis
import json
redis_cli = redis.Redis(host = 'cache', port=6379)
print(redis_cli)
# redis_cli.set('foo', 'bar')
#
# a = redis_cli.get('foo')
# print(type(a))
restaurant_484272 = {
    "name": "Ravagh",
    "type": "Persian",
    "address": {
        "street": {
            "line1": "11 E 30th St",
            "line2": "APT 1",
        },
        "city": "New York",
        "state": "NY",
        "zip": 10016,
    }
}
json_restaurant = json.dumps(restaurant_484272)
key = '18927364918278734y45'
redis_cli.set(key, json_restaurant)
response_redis = redis_cli.get(key)
response = json.loads(response_redis)
print(response)
