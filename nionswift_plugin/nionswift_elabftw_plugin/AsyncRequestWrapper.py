class AsyncRequestWrapper:

    # A static method to just wrap our calls to be run on a seperate thread
    @staticmethod
    def call_blocking_fn(fn, loop, callback, *args):

        async def async_fn_call_helper(fn, loop, *args):
            return await loop.run_in_executor(None, fn, *args)

        future = loop.create_task(async_fn_call_helper(fn, loop, *args))

        def send_result(future):
            callback(future.result())
        if callback is not None:
            future.add_done_callback(send_result)
