from flask import jsonify

def format_response(
    data={},
    input_data=None,
    status_code=200,
    status="success",
    message="Successfully received data"
):
    response = {
        "statusCode": status_code,
        "status": status,
        "message": message,
        "inputData": input_data,
        "result": data
    }
    
    return jsonify(response), status_code