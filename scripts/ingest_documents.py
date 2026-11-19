import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.session import SessionLocal
from app.rag.ingestion import ingest_file

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

DOCUMENT_REGISTRY = [
    {
        "filename": "ndma_heatwave_guidelines.pdf",
        "title": "NDMA Guidelines: Management and Prevention of Heat Waves",
        "source_url": "https://ndma.gov.in/Governance/Guidelines/Heat-Wave",
        "category": "heatwave",
        "version": "1.0",
    },
    {
        "filename": "imd_color_coded_weather_warnings.pdf",
        "title": "IMD Standard Operating Procedure: Color-Coded Weather Warnings",
        "source_url": "https://mausam.imd.gov.in/responsive/warning_guidelines.php",
        "category": "weather_alerts",
        "version": "1.0",
    },
    {
        "filename": "ndma_cyclone_safety_guidelines.pdf",
        "title": "NDMA Guidelines: Cyclone Preparedness and Safety Measures",
        "source_url": "https://ndma.gov.in/Natural-Hazards/Cyclone",
        "category": "cyclone",
        "version": "1.0",
    },
    {
        "filename": "noaa_cyclone_vs_hurricane_terminology.pdf",
        "title": "NOAA Ocean Facts: Cyclone, Hurricane, and Typhoon Terminology",
        "source_url": "https://oceanservice.noaa.gov/facts/cyclone.html",
        "category": "tropical_storms",
        "version": "1.0",
    },
    {
        "filename": "mountain_hiking_weather_safety.pdf",
        "title": "Mountain Hiking, Trekking, and High-Altitude Weather Safety Advisory",
        "source_url": "https://mausam.imd.gov.in/mountain-weather-guidelines",
        "category": "hiking_safety",
        "version": "1.0",
    },
    {
        "filename": "rain_thunderstorm_and_flood_safety.pdf",
        "title": "Urban Rain, Thunderstorm, and Monsoon Flood Safety Guidelines",
        "source_url": "https://ndma.gov.in/Natural-Hazards/Floods",
        "category": "rain_flood",
        "version": "1.0",
    },
    {
        "filename": "ndma_cold_wave_safety_guidelines.pdf",
        "title": "NDMA Guidelines: Prevention and Management of Cold Wave and Frost",
        "source_url": "https://ndma.gov.in/Natural-Hazards/Cold-Wave",
        "category": "cold_wave",
        "version": "1.0",
    },
]


def run_ingestion() -> None:
    db = SessionLocal()
    total_chunks = 0
    total_ingested = 0

    print("=" * 60)
    print("Starting Weather Intelligence Document Ingestion Pipeline")
    print("=" * 60)

    try:
        for doc in DOCUMENT_REGISTRY:
            file_path = DOCUMENTS_DIR / doc["filename"]
            if not file_path.exists():
                print(f"[MISSING] File not found: {file_path}")
                continue

            result = ingest_file(
                db=db,
                file_path=file_path,
                title=doc["title"],
                source_url=doc["source_url"],
                category=doc["category"],
                version=doc["version"],
            )

            status = result["status"]
            chunks = result["chunks_created"]
            total_chunks += chunks
            if status == "ingested":
                total_ingested += 1

            print(
                f"[{status.upper()}] {doc['title']} | Chunks: {chunks} | Category: {doc['category']}"
            )

        print("=" * 60)
        print(f"Summary: {total_ingested}/{len(DOCUMENT_REGISTRY)} documents newly ingested.")
        print(f"Total new chunks added to pgvector: {total_chunks}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()
