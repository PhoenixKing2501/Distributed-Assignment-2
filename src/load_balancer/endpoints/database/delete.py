from quart import Blueprint, current_app, jsonify, request

from common import *
from utils import *

blueprint = Blueprint('delete', __name__)


@blueprint.route('/del', methods=['DELETE'])
async def delete():
    """
    Delete a particular data entry in the distributed database.

    If `stud_id` does not exist:
        Return an error message.

    `Request payload:`
        `stud_id: id of the student whose data is to be deleted`

    `Response payload:`
        `message: Data entry with stud_id: `stud_id` removed for all replicas`
        `status: status of the request`

    `Error payload:`
        `message: error message`
        `status: status of the request`
    """

    try:
        # Get the request payload
        payload: Dict = await request.get_json()
        ic(payload)

        if payload is None:
            raise Exception('Payload is empty')

        # Get the required fields from the payload and check for errors
        stud_id: Dict = payload.get('stud_id', {})

        if len(stud_id) == 0:
            raise Exception('Payload does not contain `stud_id` field')

        # Get the shard name containing the entry
        # shard_id, shard_valid_at = 0, 0

        async with pool.acquire() as conn:
            stmt = await conn.prepare(
                '''--sql
                SELECT
                    shard_id,
                    valid_at
                FROM
                    ShardT
                WHERE
                    (stud_id_low <= ($1::INTEGER)) AND
                    (($1::INTEGER) <= stud_id_low + shard_size)
                ''')

            async with conn.transaction():
                async for record in stmt.cursor(stud_id):
                    shard_id = record["shard_id"]
                    shard_valid_at = record["valid_at"]

        if not shard_id:
            raise Exception(f'stud_id {stud_id} does not exist')

        async with lock(Read):
            async with pool.acquire() as conn:
                stmt = await conn.prepare(
                    '''--sql
                    UPDATE
                        ShardT
                    SET
                        valid_at = ($2::INTEGER)
                    WHERE
                        shard_id = ($1::INTEGER)
                    ''')

                async with conn.transaction():
                    # TODO: Change to ConsistentHashMap
                    server_names = shard_map[shard_id]

                    async with shard_locks[shard_id](Read):
                        async def wrapper(
                            session: aiohttp.ClientSession,
                            server_name: str,
                            json_payload: dict
                        ):

                            # To allow other tasks to run
                            await asyncio.sleep(0)

                            async with session.put(f'http://{server_name}:5000/del', json=json_payload) as response:
                                await response.read()

                                return response
                        # END wrapper

                        # Convert to aiohttp request
                        timeout = aiohttp.ClientTimeout(
                            connect=REQUEST_TIMEOUT)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            tasks = [asyncio.create_task(wrapper(
                                session,
                                server_name,
                                json_payload={
                                    "shard": shard_id,
                                    "stud_id": stud_id,
                                    "valid_at": shard_valid_at
                                }
                            )) for server_name in server_names]
                            serv_response = await asyncio.gather(*tasks, return_exceptions=True)
                            serv_response = serv_response[0] if not isinstance(
                                serv_response[0], BaseException) else None
                        # END async with

                        if serv_response is None:
                            raise Exception('Server did not respond')

                        serv_response = dict(await serv_response.json())
                        cur_valid_at = serv_response.get("valid_at", -1)
                        if cur_valid_at == -1:
                            raise Exception(
                                'Server response did not contain valid_at field')
                        max_valid_at = max(shard_valid_at, cur_valid_at)
                    # END async with
                    await stmt.executemany([(shard_id, max_valid_at)])
                # END async with
            # END async with
        # END async with

        # Return the response payload
        return jsonify(ic({
            'message': f"Data entry with stud_id: {stud_id} removed from all replicas",
            'status': 'success'
        })), 200

    except Exception as e:
        if DEBUG:
            print(f'{Fore.RED}ERROR | '
                  f'{e}'
                  f'{Style.RESET_ALL}',
                  file=sys.stderr)

        return jsonify(ic(err_payload(e))), 400
    # END try-except
