/**
 * offline_sync_indicator.js
 * Projeto MedIA — C5: Indicador e Armazenamento Local de Sincronização Offline
 *
 * Detecta status online/offline via navigator.onLine, gerencia IndexedDB
 * local para contingência e exibe badge visual no topo do prontuário
 * indicando "Nº de atendimentos aguardando upload".
 *
 * Conformidade SUS/APS: CIAP-2, CID-10, método SOAP, identificação CNS/CPF.
 *
 * Uso:
 *   import { OfflineSyncIndicator } from "/static/js/offline_sync_indicator.js";
 *   const indicator = new OfflineSyncIndicator({
 *     apiUploadUrl: "/api/v1/sincronizacao/atendimentos",
 *     dbName: "media_offline_v1",
 *     storeName: "atendimentos_pendentes",
 *     badgeContainerId: "media-offline-badge",
 *     prontuarioContainerId: "aba-soap",
 *   });
 *   indicator.iniciar();
 *
 * Contrato de upload (espelha backend/app/schemas/atendimento_offline.py):
 *   POST { apiUploadUrl } -> { itens: [registro...] }
 *   201 { recebidos: [id_local...], duplicados: [id_local...] }
 */

"use strict";

/**
 * Validação CNS conforme algoritmo DATASUS.
 * @param {string} cns
 * @returns {boolean}
 */
function validaCNS(cns) {
  const digits = String(cns ?? "").replace(/\D/g, "");
  if (digits.length !== 15) return false;
  if (!["1", "2", "7", "8", "9"].includes(digits[0])) return false;
  if (digits[0] === "1" || digits[0] === "2") {
    const soma = digits.split("").reduce((acc, d, i) => acc + parseInt(d) * (15 - i), 0);
    return soma % 11 === 0;
  }
  // Provisório (7,8,9): validação PIS-style
  let soma = 0;
  for (let i = 0; i < 11; i++) soma += parseInt(digits[i]) * (15 - i);
  let resto = soma % 11;
  let dv = 11 - resto;
  if (dv === 11) dv = 0;
  if (dv === 10) {
    soma += 2;
    resto = soma % 11;
    dv = 11 - resto;
  }
  return parseInt(digits[11]) === dv;
}

/**
 * Validação CPF (11 dígitos, simplificada).
 * @param {string} cpf
 * @returns {boolean}
 */
function validaCPF(cpf) {
  const digits = String(cpf ?? "").replace(/\D/g, "");
  if (digits.length !== 11 || /^(\d)\1{10}$/.test(digits)) return false;
  for (let j = 9; j < 11; j++) {
    let soma = 0;
    for (let i = 0; i <= j; i++) soma += parseInt(digits[i]) * (j + 2 - i);
    const resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) {
      if (parseInt(digits[j + 1]) !== 0) return false;
    } else if (parseInt(digits[j + 1]) !== resto) return false;
  }
  return true;
}

/**
 * Validação CIAP-2 (letra + 2 dígitos).
 * @param {string} ciap
 * @returns {boolean}
 */
function validaCIAP2(ciap) {
  return /^[A-Z]\d{2}$/i.test(ciap ?? "");
}

/**
 * Validação CID-10 (letra + até 4 caracteres alfanuméricos).
 * @param {string} cid
 * @returns {boolean}
 */
function validaCID10(cid) {
  return /^[A-Z]\d([A-Z]\d{0,2})?$/i.test(cid ?? "");
}

/**
 * Valida registro SOAP (ao menos um campo preenchido).
 * @param {Object} soap
 * @returns {boolean}
 */
function validaSOAP(soap) {
  if (!soap || typeof soap !== "object") return false;
  return ["subjetivo", "objetivo", "avaliacao", "plano"].some(
    (k) => soap[k] && String(soap[k]).trim().length > 0
  );
}

// ---------------------------------------------------------------------------
// Gerenciador IndexedDB (Promise-based)
// ---------------------------------------------------------------------------

class IndexedDBManager {
  /**
   * @param {string} dbName
   * @param {number} version
   * @param {string} storeName
   */
  constructor(dbName, version, storeName) {
    this._dbName = dbName;
    this._version = version;
    this._storeName = storeName;
    this._db = null;
  }

  /** Abre (ou cria) o banco IndexedDB. */
  async abrir() {
    if (this._db) return this._db;
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(this._dbName, this._version);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this._storeName)) {
          const store = db.createObjectStore(this._storeName, { keyPath: "id_local" });
          store.createIndex("status", "status", { unique: false });
          store.createIndex("criado_em", "criado_em", { unique: false });
        }
      };
      req.onsuccess = (e) => {
        this._db = e.target.result;
        resolve(this._db);
      };
      req.onerror = () => reject(new Error(`IndexedDB: falha ao abrir "${this._dbName}".`));
      req.onblocked = () => reject(new Error("IndexedDB bloqueado por outra aba."));
    });
  }

  /** Insere ou substitui um registro (idempotência por id_local). */
  async upsert(record) {
    const db = await this.abrir();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this._storeName, "readwrite");
      tx.objectStore(this._storeName).put(record);
      tx.oncomplete = () => resolve(record);
      tx.onerror = () => reject(tx.error);
    });
  }

  /** Lista registros pendentes, opcionalmente limitados. */
  async listarPendentes(limite = 500) {
    const db = await this.abrir();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this._storeName, "readonly");
      const store = tx.objectStore(this._storeName);
      const idx = store.index("status");
      const req = idx.getAll("PENDENTE", limite);
      req.onsuccess = () => resolve(req.result ?? []);
      req.onerror = () => reject(req.error);
    });
  }

  /** Conta registros pendentes. */
  async contarPendentes() {
    const db = await this.abrir();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this._storeName, "readonly");
      const store = tx.objectStore(this._storeName);
      const idx = store.index("status");
      const req = idx.count("PENDENTE");
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  /** Marca um registro como SINCRONIZADO. */
  async marcarSincronizado(idLocal) {
    const db = await this.abrir();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this._storeName, "readwrite");
      const store = tx.objectStore(this._storeName);
      const getReq = store.get(idLocal);
      getReq.onsuccess = () => {
        const rec = getReq.result;
        if (rec) {
          rec.status = "SINCRONIZADO";
          store.put(rec);
        }
      };
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  /**
   * Remove registros SINCRONIZADO antigos preservando os `manter` registros
   * mais recentes (ordem decrescente por `criado_em`).
   * @param {number} manter Quantidade de registros recentes a preservar.
   * @returns {Promise<void>}
   */
  async limparSincronizados(manter = 500) {
    const db = await this.abrir();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this._storeName, "readwrite");
      const store = tx.objectStore(this._storeName);
      const idx = store.index("criado_em");
      let visitados = 0;
      idx.openCursor(null, "prev").onsuccess = (e) => {
        const cursor = e.target.result;
        if (!cursor) return; // fim do cursor -> tx.oncomplete resolve
        visitados++;
        const protegido = visitados <= manter;
        if (cursor.value.status === "SINCRONIZADO" && !protegido) {
          cursor.delete();
        }
        cursor.continue();
      };
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  /** Fecha a conexão do banco. */
  fechar() {
    if (this._db) {
      this._db.close();
      this._db = null;
    }
  }
}

// ---------------------------------------------------------------------------
// Indicador de sincronização offline (badge + fila + upload)
// ---------------------------------------------------------------------------

class OfflineSyncIndicator {
  /**
   * @param {Object} opcoes
   * @param {string} [opcoes.apiUploadUrl] Endpoint POST para upload do lote.
   * @param {string} [opcoes.dbName] Nome do banco IndexedDB.
   * @param {number} [opcoes.dbVersion] Versão do schema.
   * @param {string} [opcoes.storeName] Nome da object store.
   * @param {string} [opcoes.badgeContainerId] ID do container do badge.
   * @param {string} [opcoes.prontuarioContainerId] ID do topo do prontuário (âncora do badge).
   * @param {number} [opcoes.intervaloSyncMs] Intervalo base de retry de sync.
   * @param {number} [opcoes.limiteLote] Máximo de registros por lote.
   */
  constructor(opcoes = {}) {
    /** @type {Object} Opções configuradas. */
    this._opcoes = {
      apiUploadUrl: "/api/v1/sincronizacao/atendimentos",
      dbName: "media_offline_v1",
      dbVersion: 1,
      storeName: "atendimentos_pendentes",
      badgeContainerId: "media-offline-badge",
      prontuarioContainerId: "aba-soap",
      intervaloSyncMs: 5_000,
      limiteLote: 100,
      ...opcoes,
    };

    /** @type {IndexedDBManager} */
    this._db = null;
    /** @type {boolean} Status online atual. */
    this._online = navigator.onLine;
    /** @type {number|null} Timer de retry de sync. */
    this._timerSync = null;
    /** @type {boolean} Se o módulo foi iniciado. */
    this._iniciado = false;
    /** @type {number} Contador de falhas consecutivas de sync. */
    this._falhasSync = 0;
    /** @type {AbortController|null} */
    this._ctrlAbort = null;

    // Bind dos handlers para remoção limpa de listeners.
    this._aoOnline = this._aoOnline.bind(this);
    this._aoOffline = this._aoOffline.bind(this);
    this._aoVisibility = this._aoVisibility.bind(this);
  }

  // ------------------------------------------------------------------ //
  // Inicialização                                                      //
  // ------------------------------------------------------------------ //

  /** Inicia o monitoramento online/offline, IndexedDB e o badge. */
  async iniciar() {
    if (this._iniciado) return;
    this._iniciado = true;

    this._db = new IndexedDBManager(
      this._opcoes.dbName,
      this._opcoes.dbVersion,
      this._opcoes.storeName
    );

    try {
      await this._db.abrir();
    } catch (err) {
      console.error("[OfflineSync] IndexedDB indisponível:", err.message);
      return;
    }

    // Listeners de conectividade.
    window.addEventListener("online", this._aoOnline);
    window.addEventListener("offline", this._aoOffline);
    document.addEventListener("visibilitychange", this._aoVisibility);

    // Renderiza o badge e a contagem inicial.
    await this._renderBadge();

    // Tenta sync imediato se online.
    if (this._online) {
      await this._executarSync();
    }
  }

  /** Encerra o módulo (listeners, timers, DB). */
  destruir() {
    this._iniciado = false;
    window.removeEventListener("online", this._aoOnline);
    window.removeEventListener("offline", this._aoOffline);
    document.removeEventListener("visibilitychange", this._aoVisibility);
    if (this._timerSync) {
      clearTimeout(this._timerSync);
      this._timerSync = null;
    }
    this._ctrlAbort?.abort();
    this._ctrlAbort = null;
    this._db?.fechar();
  }

  // ------------------------------------------------------------------ //
  // API pública                                                         //
  // ------------------------------------------------------------------ //

  /**
   * Registra um atendimento no IndexedDB para upload posterior.
   * @param {Object} dados Atendimento no formato SUS/APS:
   *   { id_local, cns_profissional, cns_paciente|cpf_paciente,
   *     ciap2_cod, cid10_cod, soap, data_atendimento, unidade_id }
   * @returns {Promise<Object>} Registro persistido.
   */
  async registrarAtendimento(dados) {
    if (!this._db) throw new Error("OfflineSyncIndicator não iniciado.");

    // Identificação do cidadão é obrigatória no PEC (CNS ou CPF).
    if (!dados.cns_paciente && !dados.cpf_paciente) {
      throw new Error("Identificação obrigatória: informe o CNS ou o CPF do cidadão.");
    }
    // Validação SUS/APS obrigatória.
    if (dados.cns_paciente && !validaCNS(dados.cns_paciente)) {
      throw new Error(`CNS inválido: ${dados.cns_paciente}`);
    }
    if (dados.cpf_paciente && !validaCPF(dados.cpf_paciente)) {
      throw new Error(`CPF inválido: ${dados.cpf_paciente}`);
    }
    if (dados.cns_profissional && !validaCNS(dados.cns_profissional)) {
      throw new Error(`CNS do profissional inválido: ${dados.cns_profissional}`);
    }
    if (dados.ciap2_cod && !validaCIAP2(dados.ciap2_cod)) {
      throw new Error(`CIAP-2 inválido: ${dados.ciap2_cod}`);
    }
    if (dados.cid10_cod && !validaCID10(dados.cid10_cod)) {
      throw new Error(`CID-10 inválido: ${dados.cid10_cod}`);
    }
    if (!validaSOAP(dados.soap)) {
      throw new Error("Registro SOAP inválido: ao menos um domínio (S/O/A/P) é obrigatório.");
    }

    const record = {
      id_local: dados.id_local ?? crypto.randomUUID(),
      cns_profissional: dados.cns_profissional ?? null,
      cns_paciente: dados.cns_paciente ?? null,
      cpf_paciente: dados.cpf_paciente ?? null,
      ciap2_cod: dados.ciap2_cod ?? null,
      cid10_cod: dados.cid10_cod ?? null,
      soap: { ...dados.soap },
      data_atendimento: dados.data_atendimento ?? new Date().toISOString(),
      unidade_id: dados.unidade_id ?? null,
      criado_em: new Date().toISOString(),
      tentativas_sync: 0,
      status: "PENDENTE",
    };

    await this._db.upsert(record);
    await this._renderBadge();

    // Dispara upload imediato se online.
    if (this._online) {
      this._executarSync().catch(() => {});
    }

    return record;
  }

  /**
   * Retorna a contagem de atendimentos aguardando upload.
   * @returns {Promise<number>}
   */
  async contagemPendentes() {
    if (!this._db) return 0;
    return this._db.contarPendentes();
  }

  // ------------------------------------------------------------------ //
  // Badge UI                                                           //
  // ------------------------------------------------------------------ //

  /** Cria ou atualiza o badge visual no topo do prontuário. */
  async _renderBadge() {
    let badge = document.getElementById(this._opcoes.badgeContainerId);
    if (!badge) {
      badge = document.createElement("div");
      badge.id = this._opcoes.badgeContainerId;
      badge.setAttribute("role", "status");
      badge.setAttribute("aria-live", "polite");
      badge.style.cssText =
        "position:sticky;top:0;z-index:9999;display:flex;align-items:center;gap:8px;" +
        "padding:8px 16px;border-radius:0 0 8px 8px;font-family:sans-serif;font-size:14px;" +
        "transition:background-color .3s,color .3s;";
      document.body.prepend(badge);
    }

    const pendentes = await this.contagemPendentes();
    if (!this._online) {
      badge.style.backgroundColor = "#b91c1c";
      badge.style.color = "#fff";
      badge.innerHTML =
        '<span style="width:10px;height:10px;border-radius:50%;background:#fff;display:inline-block;"></span>' +
        ` OFFLINE — ${pendentes} atendimento(s) aguardando upload`;
    } else if (pendentes > 0) {
      badge.style.backgroundColor = "#d97706";
      badge.style.color = "#fff";
      badge.innerHTML =
        '<span style="width:10px;height:10px;border-radius:50%;background:#fff;display:inline-block;"></span>' +
        ` ${pendentes} atendimento(s) aguardando sincronização`;
    } else {
      badge.style.backgroundColor = "#16a34a";
      badge.style.color = "#fff";
      badge.innerHTML =
        '<span style="width:10px;height:10px;border-radius:50%;background:#fff;display:inline-block;"></span>' +
        " Sincronizado";
    }
  }

  // ------------------------------------------------------------------ //
  // Sincronização                                                      //
  // ------------------------------------------------------------------ //

  /** Executa o upload dos registros pendentes. */
  async _executarSync() {
    if (!this._online || !this._db) return;
    if (this._ctrlAbort) this._ctrlAbort.abort();
    this._ctrlAbort = new AbortController();

    try {
      const pendentes = await this._db.listarPendentes(this._opcoes.limiteLote);
      if (pendentes.length === 0) {
        await this._renderBadge();
        return;
      }

      const resp = await fetch(this._opcoes.apiUploadUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itens: pendentes }),
        signal: this._ctrlAbort.signal,
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const resultado = await resp.json();

      // Marca como sincronizados os que foram aceitos.
      const recebidos = resultado.recebidos ?? [];
      for (const idLocal of recebidos) {
        await this._db.marcarSincronizado(idLocal);
      }

      this._falhasSync = 0;
      await this._renderBadge();

      // Limpa registros antigos sincronizados.
      await this._db.limparSincronizados(500);
    } catch (err) {
      if (err.name === "AbortError") return;
      this._falhasSync++;
      console.warn("[OfflineSync] Falha no sync:", err.message);
    }
  }

  // ------------------------------------------------------------------ //
  // Event handlers                                                     //
  // ------------------------------------------------------------------ //

  /** @param {Event} _e */
  _aoOnline(_e) {
    this._online = true;
    this._renderBadge();
    this._executarSync().catch(() => {});
  }

  /** @param {Event} _e */
  _aoOffline(_e) {
    this._online = false;
    this._renderBadge();
  }

  /** Retoma sync ao tornar a aba visível. */
  _aoVisibility() {
    if (!document.hidden && this._online) {
      this._executarSync().catch(() => {});
    }
  }
}

// Exporta para uso como módulo ES.
export { OfflineSyncIndicator, IndexedDBManager, validaCNS, validaCPF, validaCIAP2, validaCID10, validaSOAP };
export default OfflineSyncIndicator;