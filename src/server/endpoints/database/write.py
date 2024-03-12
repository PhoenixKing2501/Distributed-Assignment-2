from quart import Blueprint, current_app, jsonify, request
from colorama import Fore, Style
import sys

from consts import *
from common import *

blueprint = Blueprint('write', __name__)

@blueprint.route('/write', methods=['POST'])
async def data_write():
    """
        Write data entries to the database

        Request payload:
            "shard" : <shard_id>
            "data" : [{"stud_id": <id1>, ...},
                      {"stud_id": <id2>, ...},
                      ...
                      {"stud_id": <idn>, ...}]
            "admin": true/false
            "valid_idx" : <valid_idx>

        Response payload:
            "message": Data entries added
            "valid_idx": <valid_idx>
            "status": "success"
            
    """

    global term

    try:
        payload: dict = await request.get_json()

        valid_idx = payload.get('valid_idx', -1)

        # TBD: Apply rules, also increase the term if required

        shard_id = int(payload.get('shard', -1))
        data: list = payload.get('data', [])

        admin = False
        if payload.get('admin', '').lower() == 'true':
            admin = True
        

        # Insert the data into the database
        async with current_app.pool.acquire() as connection:
            async with connection.transaction():
                stmt = None
                if admin:
                    stmt = connection.prepare('''
                        INSERT INTO StudT (stud_id, stud_name, stud_marks, shard_id, created_at, deleted_at)
                        VALUES ($1, $2, $3, $4, $5, $6);
                    ''')
                    
                    for record_dict in data:
                        await stmt.execute(record_dict['stud_id'], record_dict['stud_name'], record_dict['stud_marks'], record_dict['shard_id'], record_dict['created_at'], record_dict['deleted_at'])
                
                else:
                    stmt = connection.prepare('''
                        INSERT INTO StudT (stud_id, stud_name, stud_marks, shard_id, created_at, deleted_at)
                        VALUES ($1, $2, $3, $4, $5, NULL);
                    ''')

                    for record_dict in data:
                        await stmt.execute(record_dict['stud_id'], record_dict['stud_name'], record_dict['stud_marks'], shard_id, term)

        # Send the response
        response_payload = {
            "message": "Data entries added",
            "valid_idx": term,
            "status": "success"
        }

        return jsonify(response_payload), 200
    
    except Exception as e:
        print(f'{Fore.RED}ERROR | '
                f'Error in data_write: {e}'
                f'{Style.RESET_ALL}',
                file=sys.stderr)
        return jsonify(ic(err_payload(e))), 400

                    


