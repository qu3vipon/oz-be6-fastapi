import asyncio
import time

async def async_function_1():
    print("비동기 함수 1 시작")
    print("sleeping...")
    # await asyncio.sleep(3)
    time.sleep(3)  # blocking...
    print("비동기 함수 1 종료")

async def async_function_2():
    print("비동기 함수 2 시작")
    print("sleeping...")
    await asyncio.sleep(3)
    print("비동기 함수 2 종료")

async def main():
    start_time = time.time()
    coro1 = async_function_1()
    coro2 = async_function_2()
    await asyncio.gather(coro1, coro2)
    end_time = time.time()
    print(end_time - start_time)

asyncio.run(main())

# python 비동기 프로그래밍 할 때
# 1) async 키워드를 통해서 코루틴 만들어준다.
# 2) 대기가 발생하는 코드에서 await 붙여준다.
#   - await가 가능한 객체 앞에
#   - 코루틴 안에서
