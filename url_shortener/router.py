import io
import urllib.parse
import requests
from fastapi.responses import FileResponse, StreamingResponse
import urllib.parse
import secrets
import string
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException
from url_shortener.models import CreateUrlShortener, CreateUrlShortenerResponse
from url_shortener.database import MockDBOperations
from starlette.responses import RedirectResponse
     
# Create the router
url_shortener = APIRouter()

# Create the database
mock_db_operations = MockDBOperations()


# This function is used to generate the short url
# Frist it validates the URL
# returns the CreatedUrlShortenerResponse

@url_shortener.post("/create", response_model=CreateUrlShortenerResponse)
async def Enter_URL(shortner: CreateUrlShortener):
    async def validate_url(url: str):
        parsed_url = urllib.parse.urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise HTTPException(status_code=400, detail="Invalid URL")
        return url
    try:
        validated_url = await validate_url(shortner.url)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    short_url = ""
    if validated_url:
        short_url_length = 7
        res = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                      for i in range(short_url_length))
        short_url = str(res)

        status = await mock_db_operations.add_data_to_db(url=validated_url, short_url=short_url)
        if not status:
            short_url = ""

    return CreateUrlShortenerResponse(short_url=short_url, url=validated_url)


# Get All urls from the database
@url_shortener.get("/list", response_model=list[CreateUrlShortenerResponse])
async def Fetch_History():
    # Get the data from the database
    data = await mock_db_operations.fetch_all_data() 
    # Create a list of CreateUrlShortenerResponse
    arr = []
    # Loop through the data
    for key, value in data.items():
        # Add the data to the list
        arr.append(CreateUrlShortenerResponse(short_url=key, url=value))
    # Return the list
    return arr

@url_shortener.get("/qrcode/{short_url}")
async def generate_qr_code(short_url: str):
    qr_code_api_url = f"https://api.qrserver.com/v1/create-qr-code/?data={short_url}"
    response = requests.get(qr_code_api_url, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to generate QR code")
    
    # Set content type as 'image/png' since the API returns PNG images
    headers = {
        "Content-Type": "image/png"
    }

    return FileResponse(response.iter_content(chunk_size=128), headers=headers)

# Delete the url from the database
@url_shortener.delete("/delete/{short_url}")
async def delete_short_url(short_url : str):
    # Delete the url from the database
    status = await mock_db_operations.delete_data_from_db(short_url = short_url)
    # If the url is deleted from the database, return the status
    if status:
        return {"message": "Successfully deleted"}
    else:
        # If the url is not deleted from the database, return the error message
        return {"message": "Failed to delete"}

# Redirect the user to the original url
@url_shortener.get("/test/{short_url}")
async def test(short_url : str):
    # Get the url from the database
    data = await mock_db_operations.fetch_all_data() 
    # Check if the url exists in the database
    if short_url in data:
        # redirect to this url
        url = data[short_url]
        # return the redirect response
        response = RedirectResponse(url=url)
        return response
    else:
        # return the error message
        return {"message": "Failed to fetch"}

    