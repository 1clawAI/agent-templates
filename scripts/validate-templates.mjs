#!/usr/bin/env node
// Local validation for agent-templates (mirrors CI checks).
// Usage: node scripts/validate-templates.mjs
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(import.meta.dirname, "..");
const TEMPLATES_DIR = join(ROOT, "templates");
const REGISTRY_PATH = join(ROOT, "registry.yaml");

const REQUIRED_MANIFEST_FIELDS = [
    "name:",
    "display_name:",
    "version:",
    "description:",
    "author:",
    "language:",
];

const SECRET_PATTERN =
    /sk-[a-zA-Z0-9]{20,}|1ck_[a-zA-Z0-9]+|ocv_[a-zA-Z0-9]+|plt_[a-zA-Z0-9]+/;

const REQUIRED_BY_LANGUAGE = {
    python: ["agent.py", "requirements.txt"],
    node: ["agent.ts", "package.json"],
};

const COMMON_FILES = ["template.yaml", "Dockerfile", "entrypoint.sh", "README.md"];

let failed = 0;
let checked = 0;

function fail(msg) {
    console.error(`FAIL: ${msg}`);
    failed++;
}

function parseRegistryNames(content) {
    const names = [];
    for (const line of content.split("\n")) {
        const m = line.match(/^\s*- name:\s*(.+)\s*$/);
        if (m) names.push(m[1].trim());
    }
    return names.sort();
}

function fieldValue(manifest, field) {
    const re = new RegExp(`^${field.replace(":", "")}:\\s*(.+)$`, "m");
    const m = manifest.match(re);
    return m ? m[1].trim().replace(/^["']|["']$/g, "") : "";
}

function listTemplateDirs() {
    return readdirSync(TEMPLATES_DIR)
        .filter((d) => {
            try {
                return (
                    statSync(join(TEMPLATES_DIR, d)).isDirectory() &&
                    existsSync(join(TEMPLATES_DIR, d, "template.yaml"))
                );
            } catch {
                return false;
            }
        })
        .sort();
}

const registryContent = readFileSync(REGISTRY_PATH, "utf-8");
const registryNames = parseRegistryNames(registryContent);
const diskNames = listTemplateDirs();

for (const name of registryNames) {
    if (!diskNames.includes(name)) {
        fail(`registry entry '${name}' has no templates/${name}/ directory`);
    }
}

for (const name of diskNames) {
    if (!registryNames.includes(name)) {
        fail(`templates/${name}/ is not listed in registry.yaml`);
    }
}

for (const name of diskNames) {
    checked++;
    const dir = join(TEMPLATES_DIR, name);
    const manifest = readFileSync(join(dir, "template.yaml"), "utf-8");

    for (const field of REQUIRED_MANIFEST_FIELDS) {
        if (!manifest.includes(field)) {
            fail(`${name} — missing required field '${field.replace(":", "")}'`);
        }
    }

    const yamlName = fieldValue(manifest, "name:");
    if (yamlName !== name) {
        fail(`${name} — template.yaml name '${yamlName}' does not match directory`);
    }

    const lang = fieldValue(manifest, "language:");
    if (lang !== "python" && lang !== "node") {
        fail(`${name} — invalid language '${lang}'`);
    }

    for (const file of [...COMMON_FILES, ...REQUIRED_BY_LANGUAGE[lang]]) {
        if (!existsSync(join(dir, file))) {
            fail(`${name} — missing required file '${file}'`);
        }
    }

    const dockerfile = readFileSync(join(dir, "Dockerfile"), "utf-8");
    if (!dockerfile.includes("HEALTHCHECK") || !dockerfile.includes("/health")) {
        fail(`${name} — Dockerfile missing HEALTHCHECK on /health`);
    }

    const entrypoint = readFileSync(join(dir, "entrypoint.sh"), "utf-8");
    if (!entrypoint.includes("ONECLAW_LLM_VIA_SHROUD")) {
        fail(`${name} — entrypoint.sh missing Shroud routing`);
    }

    const scanFiles = [
        ...REQUIRED_BY_LANGUAGE[lang],
        "Dockerfile",
        "entrypoint.sh",
        "template.yaml",
    ];
    for (const file of scanFiles) {
        const content = readFileSync(join(dir, file), "utf-8");
        if (SECRET_PATTERN.test(content)) {
            fail(`${name} — possible secret in ${file}`);
        }
    }
}

if (failed > 0) {
    console.error(`\n${failed} validation error(s) found across ${checked} templates.`);
    process.exit(1);
}

console.log(`\nAll ${checked} templates valid.`);
