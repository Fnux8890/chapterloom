use anyhow::{Context, Result, ensure};
use serde::de::{self, Deserialize, Deserializer, MapAccess, SeqAccess, Visitor};
use serde_json::{Map, Value};
use std::{
    fmt, fs, io,
    path::{Path, PathBuf},
};
use walkdir::WalkDir;

// Preserve duplicate-field errors in nested JSON, including custom reward objects.
struct Unique(Value);
impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        struct Json;
        impl<'de> Visitor<'de> for Json {
            type Value = Unique;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("a JSON value")
            }
            fn visit_unit<E>(self) -> Result<Unique, E> {
                Ok(Unique(Value::Null))
            }
            fn visit_bool<E>(self, v: bool) -> Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_i64<E>(self, v: i64) -> Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_u64<E>(self, v: u64) -> Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_f64<E>(self, v: f64) -> Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_str<E>(self, v: &str) -> Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Unique, A::Error> {
                let mut values = Vec::new();
                while let Some(Unique(v)) = seq.next_element()? {
                    values.push(v);
                }
                Ok(Unique(Value::Array(values)))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Unique, A::Error> {
                let mut values = Map::new();
                while let Some((key, Unique(v))) = map.next_entry::<String, Unique>()? {
                    if values.contains_key(&key) {
                        return Err(de::Error::custom(format!("duplicate field {key}")));
                    }
                    values.insert(key, v);
                }
                Ok(Unique(Value::Object(values)))
            }
        }
        d.deserialize_any(Json)
    }
}

pub fn read(path: &Path) -> Result<Value> {
    let text = fs::read_to_string(path).with_context(|| path.display().to_string())?;
    let Unique(v) = serde_json::from_str(text.trim_start_matches('\u{feff}'))
        .with_context(|| path.display().to_string())?;
    ensure!(v.is_object(), "{}: expected JSON object", path.display());
    Ok(v)
}

pub fn files(base: &Path) -> Result<Vec<PathBuf>> {
    let mut files = vec![];
    for entry in WalkDir::new(base).follow_links(false) {
        let e = entry?;
        ensure!(
            !e.file_type().is_symlink(),
            "symlink in pack: {}",
            e.path().display()
        );
        if e.file_type().is_file() {
            files.push(e.into_path());
        }
    }
    files.sort();
    Ok(files)
}

pub fn output_parent(dest: &Path, source: Option<&Path>) -> Result<PathBuf> {
    ensure!(!dest.try_exists()?, "{} already exists", dest.display());
    let abs = std::path::absolute(dest)?;
    let parent = abs.parent().context("expected output filename")?;
    if let Some(source) = source {
        let source = source.canonicalize()?;
        let ancestor = parent
            .ancestors()
            .find(|p| p.exists())
            .context("invalid output path")?;
        ensure!(
            !ancestor.canonicalize()?.starts_with(&source),
            "choose an output outside the source pack"
        );
    }
    fs::create_dir_all(parent)?;
    if let Some(source) = source {
        ensure!(
            !parent.canonicalize()?.starts_with(source.canonicalize()?),
            "choose an output outside the source pack"
        );
    }
    Ok(parent.to_owned())
}

pub fn archive(base: &Path, dest: &Path) -> Result<()> {
    use zip::{ZipWriter, write::SimpleFileOptions};
    let parent = output_parent(dest, Some(base))?;
    let mut temp = tempfile::NamedTempFile::new_in(parent)?;
    let mut zip = ZipWriter::new(temp.as_file_mut());
    let opts = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated)
        .last_modified_time(zip::DateTime::from_date_and_time(1980, 1, 1, 0, 0, 0).unwrap());
    let mut selected = vec![base.join("pack.mcmeta")];
    let icon = base.join("pack.png");
    if icon.is_file() {
        selected.push(icon);
    }
    let data = base.join("data");
    if data.is_dir() {
        selected.extend(files(&data)?);
    }
    selected.sort();
    for path in selected {
        ensure!(
            !path.symlink_metadata()?.is_symlink(),
            "symlink in pack: {}",
            path.display()
        );
        let rel = path.strip_prefix(base)?;
        zip.start_file(
            rel.to_str()
                .context("invalid UTF-8 path")?
                .replace('\\', "/"),
            opts,
        )?;
        io::copy(&mut fs::File::open(path)?, &mut zip)?;
    }
    zip.finish()?;
    temp.persist_noclobber(dest)?;
    Ok(())
}
